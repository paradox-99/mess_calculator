from django.contrib.auth import login
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from groups.models import GroupMembership

from .forms import ProfileForm, ProfilePasswordForm
from .models import User


def home(request):
    return render(request, "home.html")


def custom_404(request, exception):
    return render(request, "errors/404.html", status=404)


def custom_403(request, exception):
    return render(request, "errors/403.html", status=403)


class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("groups:list")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})


@login_required
def profile(request):
    membership = (
        GroupMembership.objects.filter(user=request.user, is_active=True)
        .select_related("group")
        .first()
    )
    if request.method == "POST":
        profile_form = ProfileForm(request.POST, instance=request.user, prefix="profile")
        password_form = ProfilePasswordForm(request.user, request.POST, prefix="password")
        if "profile_submit" in request.POST and profile_form.is_valid():
            profile_form.save()
            return redirect("profile")
        if "password_submit" in request.POST and password_form.is_valid():
            password_form.save()
            update_session_auth_hash(request, request.user)
            return redirect("profile")
    else:
        profile_form = ProfileForm(instance=request.user, prefix="profile")
        password_form = ProfilePasswordForm(request.user, prefix="password")
    return render(request, "accounts/profile.html", {
        "profile_form": profile_form,
        "password_form": password_form,
        "membership": membership,
    })