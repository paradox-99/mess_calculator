from django.urls import path

from . import views

app_name = "mess"

urlpatterns = [
    path("<int:group_id>/dashboard/", views.dashboard, name="dashboard"),
    path("<int:group_id>/entry/", views.entry_form, name="entry_self"),
    path("<int:group_id>/entry/<int:user_id>/", views.entry_form, name="entry_for_user"),
    path("<int:group_id>/extra-meal/<int:user_id>/", views.extra_meal_form, name="extra_meal"),
    path("<int:group_id>/logs/", views.logs_view, name="logs"),
    path("<int:group_id>/details/", views.meal_details, name="meal_details"),
    path("<int:group_id>/my-calculation/", views.personal_calculation, name="personal_calculation"),
    path("<int:group_id>/close-month/", views.close_month, name="close_month"),
]