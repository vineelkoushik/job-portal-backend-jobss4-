from rest_framework import serializers
from .models import (
    Job,
    JobApplication,
    Notification,
    Resume,
    SavedJob,
    JobAlert
)
from django.contrib.auth.models import User
class JobSerializer(serializers.ModelSerializer):

    recruiter = serializers.CharField(
        source="recruiter.username",
        read_only=True
    )

    salary = serializers.IntegerField(
        min_value=0
    )

    
    class Meta:
        model = Job
        fields = [
            "id",
            "recruiter",
            "title",
            "description",
            "company",
            "location",
            "salary",
            "job_type",
            "required_skills",
            "created_at"
        ]

        read_only_fields = [
            "id",
            "recruiter",
            "created_at"
        ]


class JobApplicationSerializer(serializers.ModelSerializer):

    job_title = serializers.CharField(
        source="job.title",
        read_only=True
    )

    company = serializers.CharField(
        source="job.company",
        read_only=True
    )

    applicant_username = serializers.CharField(
        source="applicant.username",
        read_only=True
    )

    class Meta:
        model = JobApplication

        fields = [
            "id",
            "job",
            "job_title",
            "company",
            "applicant",
            "applicant_username",
            "applied_at",
            "status"
        ]

        read_only_fields = [
            "id",
            "applicant",
            "applicant_username",
            "job_title",
            "company",
            "applied_at",
            "status"
        ]
        
class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = "__all__"
        
class ResumeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Resume
        fields = [
            "id",
            "file",
            "uploaded_at"
        ]
        
class SavedJobSerializer(serializers.ModelSerializer):

    job_title = serializers.CharField(
        source="job.title",
        read_only=True
    )

    company = serializers.CharField(
        source="job.company",
        read_only=True
    )

    class Meta:
        model = SavedJob

        fields = [
            "id",
            "job",
            "job_title",
            "company",
            "saved_at"
        ]

        read_only_fields = [
            "id",
            "saved_at",
            "job_title",
            "company"
        ]
        
class JobAlertSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    skills = serializers.CharField(
        source="user.profile.skills",
        read_only=True
    )

    location = serializers.CharField(
        source="user.profile.location",
        read_only=True
    )

    class Meta:
        model = JobAlert

        fields = [
            "id",
            "username",
            "skills",
            "location",
            "is_active",
            "created_at",
            "updated_at"
        ]

        read_only_fields = [
            "id",
            "username",
            "skills",
            "location",
            "created_at",
            "updated_at"
        ]
        
class ApplicantProfileSerializer(serializers.ModelSerializer):
    role = serializers.CharField(
        source="profile.role",
        read_only=True
    )

    phone = serializers.CharField(
        source="profile.phone",
        read_only=True
    )

    location = serializers.CharField(
        source="profile.location",
        read_only=True
    )

    skills = serializers.CharField(
        source="profile.skills",
        read_only=True
    )

    resume = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "role",
            "phone",
            "location",
            "skills",
            "resume"
        ]

    def get_resume(self, obj):
        try:
            # Try to get the resume file URL
            if hasattr(obj, 'resume') and obj.resume:
                return obj.resume.file.url
            return None
        except:
            return None