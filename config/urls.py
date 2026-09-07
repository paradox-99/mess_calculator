from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from accounts.views import custom_403, custom_404, home, profile, signup

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("signup/", signup, name="signup"),
    path("profile/", profile, name="profile"),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path("groups/", include("groups.urls", namespace="groups")),
    path("mess/", include("mess.urls", namespace="mess")),
]

handler403 = "accounts.views.custom_403"
handler404 = "accounts.views.custom_404"