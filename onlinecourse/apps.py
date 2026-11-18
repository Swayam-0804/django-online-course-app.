from django.apps import AppConfig


class OnlinecourseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "onlinecourse"
    # Shown as the section title on the admin index page.
    verbose_name = "OnlineCourse"
