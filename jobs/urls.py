from django.urls import path
from .views import (
    JobCreateView,
    JobListView,
    JobDetailView,
    JobUpdateDeleteView,
    JobApplicationCreateView,
    MyApplicationsView,
    RecruiterApplicationsView,
    ApplicationStatusUpdateView,
    RecruiterDashboardView,
    JobSeekerDashboardView,
    JobRecommendationView,
    NotificationListView,
    NotificationReadView,
    RecruiterJobListView,
    ResumeUploadView,
    SavedJobView,
    SavedJobListView,
    JobAlertView,
    ApplicantProfileView,
    RecruiterJobListView 

)

urlpatterns = [
    path("create/", JobCreateView.as_view(), name="job-create"),
    path("", JobListView.as_view(), name="job-list"),
    path("<int:id>/", JobDetailView.as_view(), name="job-detail"),
    path(
        "<int:id>/manage/",
        JobUpdateDeleteView.as_view(),
        name="job-manage"
    ),
    path(
    "<int:id>/apply/",
    JobApplicationCreateView.as_view(),
    name="job-apply"
    ),
    path(
    "applications/my/",
    MyApplicationsView.as_view(),
    name="my-applications"
    ),
    path(
    "applications/recruiter/",
    RecruiterApplicationsView.as_view(),
    name="recruiter-applications"
    ),  
    path(
    "applications/<int:id>/status/",
    ApplicationStatusUpdateView.as_view(),
    name="application-status-update"    
    ), 
    path(
    "recruiter/dashboard/",
    RecruiterDashboardView.as_view()
    ),
    path(
    "jobseeker/dashboard/",
    JobSeekerDashboardView.as_view()
    ),
    path(
    "recommendations/",
    JobRecommendationView.as_view()
    ),
    
    path(
    "notifications/",
    NotificationListView.as_view(),
    name="notifications"
    ),

    path(
        "notifications/<int:id>/read/",
        NotificationReadView.as_view(),
        name="notification-read"
    ),
    path(
    "resume/",
    ResumeUploadView.as_view(),
    name="resume-upload"
    ),
    path(
    "jobs/<int:job_id>/save/",
    SavedJobView.as_view(),
    name="save-job"
    ),

    path(
        "saved/",
        SavedJobListView.as_view(),
        name="saved-jobs"
    ),
    path(
    "job-alert/",
    JobAlertView.as_view(),
    name="job-alert"
    ),
    path(
    "applications/<int:application_id>/applicant-profile/",
    ApplicantProfileView.as_view(),
    name="applicant-profile"
    ),
    path("my/", RecruiterJobListView.as_view(), name="recruiter-jobs"),
]