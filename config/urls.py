from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
    path("login/", TemplateView.as_view(template_name="login.html"), name="login"),
    path("register/", TemplateView.as_view(template_name="register.html"), name="register"),
    path("jobs/", TemplateView.as_view(template_name="jobs.html"), name="jobs-page"),
    path("applications/", TemplateView.as_view(template_name="applications.html"), name="applications-page"),
    path("dashboard/", TemplateView.as_view(template_name="dashboard.html"), name="dashboard-page"),
    path("recruiter/", TemplateView.as_view(template_name="recruiter.html"), name="recruiter-page"),
    path("profile/", TemplateView.as_view(template_name="profile.html"), name="profile-page"),
    path("saved-jobs/", TemplateView.as_view(template_name="saved_jobs.html"), name="saved-jobs"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/jobs/", include("jobs.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)