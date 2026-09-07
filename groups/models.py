import secrets

from django.conf import settings
from django.db import models


def generate_invite_code():
    return secrets.token_urlsafe(6)[:8]


class Group(models.Model):
    name = models.CharField(max_length=100)
    invite_code = models.CharField(max_length=12, unique=True, default=generate_invite_code)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="groups_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class GroupMembership(models.Model):
    class Role(models.TextChoices):
        LEADER = "leader", "Leader"
        MEMBER = "member", "Member"

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("group", "user")

    def __str__(self):
        return f"{self.user} in {self.group} ({self.role})"