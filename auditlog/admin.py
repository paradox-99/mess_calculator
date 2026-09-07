from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp", "group", "actor", "target_user",
        "entry_date", "action", "field_name", "old_value", "new_value",
    )
    list_filter = ("group", "action", "field_name")
    date_hierarchy = "timestamp"

    # Read-only surface: logs are only ever written by mess.services.record_daily_entry
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False