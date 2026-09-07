from django import forms
from django.contrib.auth.forms import PasswordChangeForm

from .models import User


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")


class ProfilePasswordForm(PasswordChangeForm):
    pass
