from django.conf import settings
from django.db import models

from groups.models import Group


class ActivityLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="logs")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    entry_date = models.DateField()
    action = models.CharField(max_length=10, choices=Action.choices)
    field_name = models.CharField(max_length=20)  # "lunch" / "dinner" / "cost"
    old_value = models.CharField(max_length=50, null=True, blank=True)
    new_value = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.actor} {self.action} {self.field_name} on {self.target_user}/{self.entry_date}"

    # Defense in depth: append-only even if someone bypasses the admin/views
    # and touches the ORM directly (shell, a future careless view, etc).
    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("ActivityLog entries are append-only and cannot be edited.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("ActivityLog entries are append-only and cannot be deleted.")