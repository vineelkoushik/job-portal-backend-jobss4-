from django.db import models
from django.contrib.auth.models import User


class Job(models.Model):

    JOB_TYPE_CHOICES = [
        ("FULL_TIME", "Full Time"),
        ("PART_TIME", "Part Time"),
        ("INTERNSHIP", "Internship"),
    ]

    recruiter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="jobs"
    )

    title = models.CharField(max_length=200)

    description = models.TextField()

    company = models.CharField(max_length=200)

    location = models.CharField(max_length=100)

    salary = models.IntegerField()

    job_type = models.CharField(
        max_length=20,
        choices=JOB_TYPE_CHOICES
    )

    required_skills = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title

from django.contrib.auth.models import User
from django.db import models


class JobApplication(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SHORTLISTED", "Shortlisted"),
        ("REJECTED", "Rejected"),
        ("HIRED", "Hired"),
    ]

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="applications"
    )

    applicant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="job_applications"
    )

    applied_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    def __str__(self):
        return f"{self.applicant.username} - {self.job.title}"


class Notification(models.Model):

    NOTIFICATION_TYPES = [
        ("APPLICATION_SUBMITTED", "Application Submitted"),
        ("APPLICATION_SHORTLISTED", "Application Shortlisted"),
        ("APPLICATION_REJECTED", "Application Rejected"),
        ("APPLICATION_HIRED", "Application Hired"),
        ("NEW_APPLICATION", "New Application"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.notification_type}"
    
class Resume(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="resume"
    )

    file = models.FileField(
        upload_to="resumes/"
    )

    uploaded_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.user.username} Resume"

class SavedJob(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="saved_jobs"
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="saved_by"
    )

    saved_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "job"],
                name="unique_saved_job"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.job.title}"
    
class JobAlert(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="job_alert"
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.user.username} Job Alert"