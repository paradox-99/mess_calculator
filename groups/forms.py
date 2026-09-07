from django import forms

from accounts.models import User

from .models import Group
from .models import GroupMembership

class GroupCreateForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name"]


class GroupJoinForm(forms.Form):
    invite_code = forms.CharField(max_length=12, label="Invite code")

    def clean_invite_code(self):
        code = self.cleaned_data["invite_code"].strip()
        try:
            self.cleaned_data["group"] = Group.objects.get(invite_code=code)
        except Group.DoesNotExist:
            raise forms.ValidationError("No group found with that invite code.")
        return code


class MemberUsernameForm(forms.Form):
    username = forms.CharField(max_length=150, label="Username")

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        try:
            return User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            raise forms.ValidationError("No user found with that username.")


class LeadershipTransferForm(forms.Form):
    member = forms.ModelChoiceField(queryset=User.objects.none(), label="New leader")

    def __init__(self, *args, group=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["member"].queryset = User.objects.filter(
            memberships__group=group,
            memberships__is_active=True,
            memberships__role=GroupMembership.Role.MEMBER,
        ).order_by("username")