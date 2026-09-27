from django.urls import path

from . import views

app_name = "shop"

urlpatterns = [
    path("", views.index, name="index"),
    path("jobs/new", views.new_job, name="new"),
    path("jobs/create", views.create_job, name="create"),
    path("jobs/<int:job_id>", views.detail, name="detail"),
    path("jobs/<int:job_id>/edit", views.edit_job, name="edit"),
    path("jobs/<int:job_id>/update", views.update_job, name="update"),
    path("jobs/<int:job_id>/status", views.set_status, name="status"),
    path("jobs/<int:job_id>/delete", views.delete_job, name="delete"),
]
