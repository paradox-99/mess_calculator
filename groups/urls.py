from django.urls import path

from . import views

app_name = "groups"

urlpatterns = [
    path("", views.group_list, name="list"),
    path("create/", views.group_create, name="create"),
    path("join/", views.group_join, name="join"),
    path("<int:group_id>/members/add/", views.add_member, name="add_member"),
    path("<int:group_id>/members/<int:user_id>/remove/", views.remove_member, name="remove_member"),
    path("<int:group_id>/transfer-leadership/", views.transfer_leadership, name="transfer_leadership"),
]