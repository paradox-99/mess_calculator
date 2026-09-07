from django.core.exceptions import PermissionDenied
from django.db import transaction

from auditlog.models import ActivityLog
from groups.permissions import can_edit_entry

from .models import DailyEntry, MonthCycle

TRACKED_FIELDS = ("lunch", "dinner", "cost")


@transaction.atomic
def record_daily_entry(*, actor, group, target_user, date, lunch=None, dinner=None, cost=None):
    """
    Create or update one member's DailyEntry for a date. This is the ONLY
    path views/forms should use to touch DailyEntry — never call
    DailyEntry.objects.create()/save() directly from a view, or the audit
    trail goes stale and the permission rule isn't enforced.

    Pass only the fields that changed (leave the rest as None) — only those
    get diffed and logged.
    """
    if not can_edit_entry(actor, group, target_user):
        raise PermissionDenied(
            f"{actor} is not allowed to edit {target_user}'s mess entries in {group}."
        )

    month_cycle, _ = MonthCycle.objects.get_or_create(
        group=group, year=date.year, month=date.month
    )
    if month_cycle.is_closed:
        raise PermissionDenied("This month's calculation is closed.")
    entry, created = DailyEntry.objects.get_or_create(
        month_cycle=month_cycle, user=target_user, date=date
    )

    incoming = {"lunch": lunch, "dinner": dinner, "cost": cost}
    changed_fields = []
    for field, new_value in incoming.items():
        if new_value is None:
            continue
        old_value = getattr(entry, field)
        if old_value != new_value:
            changed_fields.append((field, old_value, new_value))
            setattr(entry, field, new_value)

    if changed_fields:
        entry.save()

    action = ActivityLog.Action.CREATE if created else ActivityLog.Action.UPDATE
    for field, old_value, new_value in changed_fields:
        ActivityLog.objects.create(
            group=group,
            actor=actor,
            target_user=target_user,
            entry_date=date,
            action=action,
            field_name=field,
            old_value=None if created else str(old_value),
            new_value=str(new_value),
        )

    return entry


def add_extra_meal(*, actor, group, target_user, date, meal_type, quantity):
    """Increment one member's lunch or dinner count and audit the change."""
    if meal_type not in ("lunch", "dinner"):
        raise ValueError("meal_type must be lunch or dinner")
    if not can_edit_entry(actor, group, target_user):
        raise PermissionDenied(
            f"{actor} is not allowed to edit {target_user}'s mess entries in {group}."
        )

    month_cycle, _ = MonthCycle.objects.get_or_create(
        group=group, year=date.year, month=date.month
    )
    if month_cycle.is_closed:
        raise PermissionDenied("This month's calculation is closed.")
    entry, _ = DailyEntry.objects.get_or_create(
        month_cycle=month_cycle, user=target_user, date=date
    )
    new_value = getattr(entry, meal_type) + quantity
    values = {"lunch": None, "dinner": None, "cost": None}
    values[meal_type] = new_value
    return record_daily_entry(
        actor=actor,
        group=group,
        target_user=target_user,
        date=date,
        **values,
    )