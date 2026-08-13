from jobs.serializers import NotificationSerializer
from jobs.serializers import NotificationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from django.db import models
import os  # <-- ADDED for filename handling
from .models import (
    Job,
    JobApplication,
    Notification,
    Resume,
    SavedJob,
    JobAlert
)
from .serializers import (
    JobSerializer,
    JobApplicationSerializer,
    NotificationSerializer,
    ResumeSerializer,
    SavedJobSerializer,
    JobAlertSerializer,
    ApplicantProfileSerializer
)
from rest_framework.pagination import PageNumberPagination


class JobCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        # Only recruiters can create jobs
        if request.user.profile.role != "RECRUITER":
            return Response(
                {
                    "error": "Only recruiters can create jobs"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = JobSerializer(data=request.data)

        if serializer.is_valid():

            job = serializer.save(
                recruiter=request.user
            )

            # ---------------------------------------
            # JOB ALERT MATCHING
            # ---------------------------------------

            job_skills = [
                skill.strip().lower()
                for skill in job.required_skills.split(",")
                if skill.strip()
            ]

            alerts = JobAlert.objects.filter(
                is_active=True
            ).select_related(
                "user",
                "user__profile"
            )

            for alert in alerts:

                profile = alert.user.profile

                if not profile.skills:
                    continue

                seeker_skills = [
                    skill.strip().lower()
                    for skill in profile.skills.split(",")
                    if skill.strip()
                ]

                # Check skill match
                skill_match = any(
                    seeker_skill in job_skill
                    or job_skill in seeker_skill
                    for seeker_skill in seeker_skills
                    for job_skill in job_skills
                )

                # Check location match
                location_match = (
                    not profile.location
                    or
                    profile.location.strip().lower()
                    ==
                    job.location.strip().lower()
                )

                # Create notification when both match
                if skill_match and location_match:

                    Notification.objects.create(
                        user=alert.user,
                        notification_type="JOB_ALERT",
                        message=(
                            f"A new job '{job.title}' at "
                            f"{job.company} matches your profile."
                        )
                    )

            # ---------------------------------------
            # RETURN CREATED JOB
            # ---------------------------------------

            return Response(
                JobSerializer(job).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class JobListView(APIView):

    def get(self, request):

        jobs = Job.objects.all()

        # Search by title, description, company or required skills
        search = request.query_params.get("search")

        if search:
            jobs = jobs.filter(
                models.Q(title__icontains=search)
                | models.Q(description__icontains=search)
                | models.Q(company__icontains=search)
                | models.Q(required_skills__icontains=search)
            )

        # Filter by location
        location = request.query_params.get("location")

        if location:
            jobs = jobs.filter(
                location__icontains=location
            )

        # Filter by job type
        job_type = request.query_params.get("job_type")

        if job_type:
            jobs = jobs.filter(
                job_type=job_type
            )

        ordering = request.query_params.get("ordering")
        print("ORDERING RECEIVED:", ordering)

        allowed_ordering = [
        "created_at",
        "-created_at",
        "salary",
        "-salary"
        ]

        if ordering in allowed_ordering:
            jobs = jobs.order_by(ordering)
        else:
            jobs = jobs.order_by("-created_at")

        # Pagination
        paginator = PageNumberPagination()

        paginated_jobs = paginator.paginate_queryset(
            jobs,
            request
        )

        serializer = JobSerializer(
            paginated_jobs,
            many=True
        )

        return paginator.get_paginated_response(
            serializer.data
        )


class JobDetailView(APIView):

    def get(self, request, id):

        try:
            job = Job.objects.get(id=id)
        except Job.DoesNotExist:
            return Response(
                {"error": "Job not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = JobSerializer(job)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class JobUpdateDeleteView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, id):

        try:
            job = Job.objects.get(id=id)
        except Job.DoesNotExist:
            return Response(
                {"error": "Job not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if job.recruiter != request.user:
            return Response(
                {"error": "You can only update your own jobs"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = JobSerializer(
            job,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, id):

        try:
            job = Job.objects.get(id=id)
        except Job.DoesNotExist:
            return Response(
                {"error": "Job not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if job.recruiter != request.user:
            return Response(
                {"error": "You can only delete your own jobs"},
                status=status.HTTP_403_FORBIDDEN
            )

        job.delete()

        return Response(
        {"message": "Job deleted successfully"},
        status=status.HTTP_200_OK
    )


class JobApplicationCreateView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, id):

        # 1. Only Job Seekers can apply
        if request.user.profile.role != "JOB_SEEKER":
            return Response(
                {"error": "Only job seekers can apply"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2. Check whether the job exists
        try:
            job = Job.objects.get(id=id)

        except Job.DoesNotExist:
            return Response(
                {"error": "Job not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 3. Prevent duplicate applications
        if JobApplication.objects.filter(
            job=job,
            applicant=request.user
        ).exists():

            return Response(
                {"error": "You have already applied for this job"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Create application
        application = JobApplication.objects.create(
            job=job,
            applicant=request.user
        )

        Notification.objects.create(
        user=job.recruiter,
        notification_type="NEW_APPLICATION",
        message=f"{request.user.username} applied for your job: {job.title}"
        )

        # 5. Return application details
        serializer = JobApplicationSerializer(application)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


class MyApplicationsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Only Job Seekers can view their applications
        if request.user.profile.role != "JOB_SEEKER":
            return Response(
                {"error": "Only job seekers can view applications"},
                status=status.HTTP_403_FORBIDDEN
            )

        applications = JobApplication.objects.filter(
            applicant=request.user
        ).order_by("-applied_at")

        serializer = JobApplicationSerializer(
            applications,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class RecruiterApplicationsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        # 1. Only recruiters can access this endpoint
        if request.user.profile.role != "RECRUITER":
            return Response(
                {"error": "Only recruiters can view applications"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2. Get all jobs created by this recruiter
        jobs = Job.objects.filter(
            recruiter=request.user
        )

        # 3. Get applications for those jobs
        applications = JobApplication.objects.filter(
        job__in=jobs
        )

        # Filter by application status
        status_filter = request.query_params.get("status")

        if status_filter:
            applications = applications.filter(
                status=status_filter
            )

            # Filter by specific job
        job_id = request.query_params.get("job")

        if job_id:
            applications = applications.filter(
            job__id=job_id
            )

        applications = applications.order_by("-applied_at")

        # 4. Serialize applications
        serializer = JobApplicationSerializer(
            applications,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class ApplicationStatusUpdateView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, id):

        # 1. Only recruiters can change application status
        if request.user.profile.role != "RECRUITER":
            return Response(
                {"error": "Only recruiters can update application status"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2. Find the application
        try:
            application = JobApplication.objects.get(id=id)

        except JobApplication.DoesNotExist:
            return Response(
                {"error": "Application not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 3. Make sure the recruiter owns the job
        if application.job.recruiter != request.user:
            return Response(
                {"error": "You can only update applications for your own jobs"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 4. Get the new status
        new_status = request.data.get("status")

        # 5. Validate the status
        valid_statuses = [
            "PENDING",
            "SHORTLISTED",
            "REJECTED",
            "HIRED"
        ]

        if new_status not in valid_statuses:
            return Response(
                {
                    "error": "Invalid status",
                    "allowed_statuses": valid_statuses
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # 6. Update status
        application.status = new_status
        application.save()

        notification_messages = {
        "SHORTLISTED": f"Your application for {application.job.title} has been shortlisted.",
        "REJECTED": f"Your application for {application.job.title} has been rejected.",
        "HIRED": f"Congratulations! You have been hired for {application.job.title}."
    }

        notification_types = {
            "SHORTLISTED": "APPLICATION_SHORTLISTED",
            "REJECTED": "APPLICATION_REJECTED",
            "HIRED": "APPLICATION_HIRED"
        }

        if new_status in notification_messages:

            Notification.objects.create(
                user=application.applicant,
                notification_type=notification_types[new_status],
                message=notification_messages[new_status]
            )

        # 7. Return updated application
        serializer = JobApplicationSerializer(application)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class RecruiterDashboardView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        if request.user.profile.role != "RECRUITER":
            return Response(
                {"error": "Only recruiters can access dashboard"},
                status=status.HTTP_403_FORBIDDEN
            )

        jobs = Job.objects.filter(
            recruiter=request.user
        )

        applications = JobApplication.objects.filter(
            job__in=jobs
        )

        return Response(
            {
                "total_jobs": jobs.count(),
                "total_applications": applications.count(),
                "pending": applications.filter(
                    status="PENDING"
                ).count(),
                "shortlisted": applications.filter(
                    status="SHORTLISTED"
                ).count(),
                "rejected": applications.filter(
                    status="REJECTED"
                ).count(),
                "hired": applications.filter(
                    status="HIRED"
                ).count()
            },
            status=status.HTTP_200_OK
        )


class JobSeekerDashboardView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        if request.user.profile.role != "JOB_SEEKER":
            return Response(
                {"error": "Only job seekers can access dashboard"},
                status=status.HTTP_403_FORBIDDEN
            )

        applications = JobApplication.objects.filter(
            applicant=request.user
        )

        return Response(
            {
                "total_applications": applications.count(),
                "pending": applications.filter(
                    status="PENDING"
                ).count(),
                "shortlisted": applications.filter(
                    status="SHORTLISTED"
                ).count(),
                "rejected": applications.filter(
                    status="REJECTED"
                ).count(),
                "hired": applications.filter(
                    status="HIRED"
                ).count()
            },
            status=status.HTTP_200_OK
        )


class JobRecommendationView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Only Job Seekers can get recommendations
        if request.user.profile.role != "JOB_SEEKER":
            return Response(
                {"error": "Only job seekers can get recommendations"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get the user's skills
        user_skills = request.user.profile.skills
        user_location = request.user.profile.location
        if not user_skills:
            return Response(
                {
                    "message": "Please add your skills to your profile"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Convert skills into a list
        skills = [
            skill.strip().lower()
            for skill in user_skills.split(",")
            if skill.strip()
        ]

        # Normalize common skill names
        skill_aliases = {
            "drf": "django rest framework",
            "django-rest-framework": "django rest framework",
            "react.js": "react",
            "reactjs": "react",
            "node": "node.js",
            "nodejs": "node.js",
            "postgres": "postgresql"
        }

        # Normalize user's skills
        normalized_user_skills = [
            skill_aliases.get(skill, skill)
            for skill in skills
        ]

        # Get all jobs
        # 6. Get jobs the user has already applied for
        applied_job_ids = JobApplication.objects.filter(
            applicant=request.user
        ).values_list(
            "job_id",
            flat=True
        )

        # Get jobs excluding already applied jobs
        jobs = Job.objects.exclude(
            id__in=applied_job_ids
        )

        recommended_jobs = []

        for job in jobs:

            required_skills = [
                skill.strip().lower()
                for skill in job.required_skills.split(",")
                if skill.strip()
            ]

            # Skip jobs with no required skills
            if not required_skills:
                continue

            # Normalize job's required skills
            normalized_required_skills = [
                skill_aliases.get(skill, skill)
                for skill in required_skills
            ]

            # Find matching skills
            matching_skills = [
                skill
                for skill in normalized_user_skills
                if skill in normalized_required_skills
            ]

            # Remove duplicates
            matching_skills = list(
                dict.fromkeys(matching_skills)
            )

            if matching_skills:
                skill_match_percentage = (
                len(matching_skills) /
                len(normalized_required_skills)
                ) * 100

                # Check location match
                location_match = False

                if user_location and job.location:

                    if user_location.strip().lower() == job.location.strip().lower():
                        location_match = True

                # Final recommendation score
                match_percentage = skill_match_percentage

                if location_match:
                    match_percentage += 20

                # Maximum score should remain 100
                match_percentage = min(match_percentage, 100)

                # Only recommend jobs with at least 30% match
                if match_percentage >= 30:

                    recommended_jobs.append({
                    "job": JobSerializer(job).data,
                    "matching_skills": matching_skills,
                    "match_count": len(matching_skills),
                    "skill_match_percentage": round(
                        skill_match_percentage,
                        2
                    ),
                    "location_match": location_match,
                    "match_percentage": round(
                        match_percentage,
                        2
                    )
                })

        # Highest match percentage first
        recommended_jobs.sort(
            key=lambda x: x["match_percentage"],
            reverse=True
        )

        return Response(
            recommended_jobs,
            status=status.HTTP_200_OK
        )


class NotificationListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        notifications = Notification.objects.filter(
            user=request.user
        ).order_by("-created_at")

        serializer = NotificationSerializer(
            notifications,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class NotificationReadView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, id):

        try:
            notification = Notification.objects.get(
                id=id,
                user=request.user
            )

        except Notification.DoesNotExist:

            return Response(
                {"error": "Notification not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        notification.is_read = True
        notification.save()

        serializer = NotificationSerializer(
            notification
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


# ======================================================
# UPDATED ResumeUploadView – with override & filename
# ======================================================
class ResumeUploadView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Only Job Seekers can upload resumes
        if request.user.profile.role != "JOB_SEEKER":
            return Response(
                {
                    "error": "Only job seekers can upload resumes"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Check whether a file was uploaded
        if "file" not in request.FILES:
            return Response(
                {
                    "error": "Please upload a resume file"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create resume – this OVERRIDES the old file
        resume, created = Resume.objects.get_or_create(user=request.user)
        resume.file = request.FILES["file"]
        resume.save()

        # Serialize and add filename to response
        serializer = ResumeSerializer(resume)
        response_data = serializer.data
        response_data["filename"] = os.path.basename(resume.file.name)

        return Response(
            response_data,
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED
        )

    def get(self, request):
        # Only Job Seekers can view their resume
        if request.user.profile.role != "JOB_SEEKER":
            return Response(
                {
                    "error": "Only job seekers can view resumes"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            resume = Resume.objects.get(
                user=request.user
            )
        except Resume.DoesNotExist:
            return Response(
                {
                    "error": "Resume not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ResumeSerializer(resume)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def patch(self, request):
        # Only Job Seekers can update resumes
        if request.user.profile.role != "JOB_SEEKER":
            return Response(
                {
                    "error": "Only job seekers can update resumes"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            resume = Resume.objects.get(
                user=request.user
            )
        except Resume.DoesNotExist:
            return Response(
                {
                    "error": "Resume not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Make sure a new file was provided
        if "file" not in request.FILES:
            return Response(
                {
                    "error": "Please upload a new resume file"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ResumeSerializer(
            resume,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request):
        # Only Job Seekers can delete resumes
        if request.user.profile.role != "JOB_SEEKER":
            return Response(
                {
                    "error": "Only job seekers can delete resumes"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            resume = Resume.objects.get(
                user=request.user
            )
        except Resume.DoesNotExist:
            return Response(
                {
                    "error": "Resume not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        resume.delete()

        return Response(
            {
                "message": "Resume deleted successfully"
            },
            status=status.HTTP_200_OK
        )


# ======================================================
# SAVED JOBS
# ======================================================
class SavedJobView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):

        if request.user.profile.role != "JOB_SEEKER":
            return Response(
                {
                    "error": "Only job seekers can save jobs"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            job = Job.objects.get(id=job_id)

        except Job.DoesNotExist:
            return Response(
                {
                    "error": "Job not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        saved_job, created = SavedJob.objects.get_or_create(
            user=request.user,
            job=job
        )

        if not created:
            return Response(
                {
                    "message": "Job already saved"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = SavedJobSerializer(saved_job)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, job_id):

        if request.user.profile.role != "JOB_SEEKER":
            return Response(
                {
                    "error": "Only job seekers can remove saved jobs"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            saved_job = SavedJob.objects.get(
                user=request.user,
                job_id=job_id
            )

        except SavedJob.DoesNotExist:
            return Response(
                {
                    "error": "Job is not saved"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        saved_job.delete()

        return Response(
            {
                "message": "Job removed from saved jobs"
            },
            status=status.HTTP_200_OK
        )


class SavedJobListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        if request.user.profile.role != "JOB_SEEKER":
            return Response(
                {
                    "error": "Only job seekers can view saved jobs"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        saved_jobs = SavedJob.objects.filter(
            user=request.user
        ).order_by("-saved_at")

        serializer = SavedJobSerializer(
            saved_jobs,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

class RecruiterJobListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Only recruiters can access this
        if request.user.profile.role != "RECRUITER":
            return Response(
                {"error": "Only recruiters can view their jobs"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all jobs created by this recruiter
        jobs = Job.objects.filter(
            recruiter=request.user
        ).order_by("-created_at")

        serializer = JobSerializer(jobs, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
# ======================================================
# JOB ALERTS
# ======================================================
class JobAlertView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        if request.user.profile.role != "JOB_SEEKER":
            return Response(
                {
                    "error": "Only job seekers can use job alerts"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        alert = JobAlert.objects.filter(
            user=request.user
        ).first()

        if not alert:
            return Response(
                {
                    "message": "Job alert is not enabled"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = JobAlertSerializer(alert)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def post(self, request):

        if request.user.profile.role != "JOB_SEEKER":
            return Response(
                {
                    "error": "Only job seekers can enable job alerts"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.user.profile.skills:
            return Response(
                {
                    "error": "Please add skills to your profile first"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        alert, created = JobAlert.objects.get_or_create(
            user=request.user
        )

        if not created and alert.is_active:
            return Response(
                {
                    "message": "Job alert is already enabled"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        alert.is_active = True
        alert.save()

        serializer = JobAlertSerializer(alert)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def patch(self, request):

        if request.user.profile.role != "JOB_SEEKER":
            return Response(
                {
                    "error": "Only job seekers can manage job alerts"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        alert = JobAlert.objects.filter(
            user=request.user
        ).first()

        if not alert:
            return Response(
                {
                    "error": "Job alert is not enabled"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if "is_active" in request.data:

            alert.is_active = request.data["is_active"]

            alert.save()

        serializer = JobAlertSerializer(alert)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def delete(self, request):

        if request.user.profile.role != "JOB_SEEKER":
            return Response(
                {
                    "error": "Only job seekers can delete job alerts"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        alert = JobAlert.objects.filter(
            user=request.user
        ).first()

        if not alert:
            return Response(
                {
                    "error": "Job alert not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        alert.delete()

        return Response(
            {
                "message": "Job alert disabled"
            },
            status=status.HTTP_200_OK
        )


# ======================================================
# APPLICANT PROFILE VIEW (FOR RECRUITERS)
# ======================================================
# Add this import at the top of jobs/views.py
from .models import Resume

class ApplicantProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, application_id):
        # Only recruiters can view applicant profiles
        if request.user.profile.role != "RECRUITER":
            return Response(
                {
                    "error": "Only recruiters can view applicant profiles"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Find the application
        application = JobApplication.objects.filter(
            id=application_id
        ).select_related(
            "job",
            "applicant",
            "applicant__profile"
        ).first()

        if not application:
            return Response(
                {
                    "error": "Application not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Make sure the job belongs to this recruiter
        if application.job.recruiter != request.user:
            return Response(
                {
                    "error": "You can only view applicants for your own jobs"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        applicant = application.applicant

        # Get the resume URL if it exists
        resume_url = None
        try:
            resume = Resume.objects.get(user=applicant)
            resume_url = resume.file.url
        except Resume.DoesNotExist:
            pass

        serializer = ApplicantProfileSerializer(applicant)
        response_data = serializer.data
        response_data['resume'] = resume_url

        return Response(
            response_data,
            status=status.HTTP_200_OK
        )