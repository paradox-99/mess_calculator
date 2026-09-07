# All writes to DailyEntry go through mess.services.record_daily_entry —
# never DailyEntry.objects.create()/save() directly from a view — so the
# audit log and the leader/member permission rule can't be bypassed.
from datetime import date as date_cls
from calendar import monthrange
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from groups.models import GroupMembership
from groups.permissions import can_view_logs, is_leader
from groups.utils import get_member_group_or_404

from .forms import DailyEntryForm, ExtraMealForm
from .models import MonthCycle
from .services import add_extra_meal, record_daily_entry


@login_required
def dashboard(request, group_id):
    group = get_member_group_or_404(request.user, group_id)

    today = date_cls.today()
    year, month = _month_from_request(request)

    month_cycle, _ = MonthCycle.objects.get_or_create(group=group, year=year, month=month)

    members = User.objects.filter(
        memberships__group=group, memberships__is_active=True
    ).distinct()
    rows = [{"user": member, **month_cycle.balance_for(member)} for member in members]

    prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)
    next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)
    month_label = date_cls(year, month, 1).strftime("%B, %Y")
    available_months = [
        {
            "value": f"{cycle.year:04d}-{cycle.month:02d}",
            "label": date_cls(cycle.year, cycle.month, 1).strftime("%B, %Y"),
        }
        for cycle in MonthCycle.objects.filter(group=group).order_by("-year", "-month")
    ]
    selected_month = f"{year:04d}-{month:02d}"
    if not any(item["value"] == selected_month for item in available_months):
        available_months.insert(0, {"value": selected_month, "label": month_label})

    context = {
        "group": group,
        "month_cycle": month_cycle,
        "month_label": month_label,
        "available_months": available_months,
        "selected_month": selected_month,
        "today": today,
        "is_current_month": year == today.year and month == today.month,
        "is_past_month": (year, month) < (today.year, today.month),
        "close_status": request.GET.get("close"),
        "rows": rows,
        "is_leader": is_leader(request.user, group),
        "prev_month": prev_month, "prev_year": prev_year,
        "next_month": next_month, "next_year": next_year,
    }
    return render(request, "mess/dashboard.html", context)


def _month_from_request(request):
    today = date_cls.today()
    params = request.GET if request.method == "GET" else request.POST
    selected_month = params.get("month_choice")
    if selected_month:
        try:
            year, month = (int(value) for value in selected_month.split("-", 1))
        except (TypeError, ValueError):
            year, month = today.year, today.month
    else:
        try:
            year = int(params.get("year", today.year))
            month = int(params.get("month", today.month))
        except (TypeError, ValueError):
            year, month = today.year, today.month
    if not 1 <= month <= 12 or not 1 <= year <= 9999:
        return today.year, today.month
    return year, month


@login_required
def meal_details(request, group_id):
    group = get_member_group_or_404(request.user, group_id)
    year, month = _month_from_request(request)
    month_cycle, _ = MonthCycle.objects.get_or_create(group=group, year=year, month=month)
    members = list(
        User.objects.filter(
            memberships__group=group, memberships__is_active=True
        ).distinct().order_by("username")
    )
    entries = month_cycle.entries.select_related("user").order_by("date", "user__username")
    entry_map = {(entry.date, entry.user_id): entry for entry in entries}
    extra_meals = {member.pk: Decimal("0") for member in members}
    for entry in entries:
        if entry.user_id not in extra_meals:
            continue
        extra_meals[entry.user_id] += max(entry.lunch - Decimal("1"), Decimal("0"))
        extra_meals[entry.user_id] += max(entry.dinner - Decimal("1"), Decimal("0"))
    detail_rows = []
    for day in range(1, monthrange(year, month)[1] + 1):
        entry_date = date_cls(year, month, day)
        detail_rows.append({
            "date": entry_date,
            "cells": [entry_map.get((entry_date, member.pk)) for member in members],
        })
    month_label = date_cls(year, month, 1).strftime("%B, %Y")
    available_months = [
        {
            "value": f"{cycle.year:04d}-{cycle.month:02d}",
            "label": date_cls(cycle.year, cycle.month, 1).strftime("%B, %Y"),
        }
        for cycle in MonthCycle.objects.filter(group=group).order_by("-year", "-month")
    ]
    selected_month = f"{year:04d}-{month:02d}"
    if not any(item["value"] == selected_month for item in available_months):
        available_months.insert(0, {"value": selected_month, "label": month_label})
    return render(request, "mess/meal_details.html", {
        "group": group,
        "month_cycle": month_cycle,
        "month_label": month_label,
        "available_months": available_months,
        "selected_month": selected_month,
        "members": members,
        "extra_meals": [
            {"user": member, "count": extra_meals[member.pk]} for member in members
        ],
        "detail_rows": detail_rows,
        "year": year,
        "month": month,
    })


@login_required
def personal_calculation(request, group_id):
    group = get_member_group_or_404(request.user, group_id)
    year, month = _month_from_request(request)
    month_cycle, _ = MonthCycle.objects.get_or_create(group=group, year=year, month=month)
    summary = month_cycle.balance_for(request.user)
    month_label = date_cls(year, month, 1).strftime("%B, %Y")
    return render(request, "mess/personal_calculation.html", {
        "group": group,
        "month_cycle": month_cycle,
        "month_label": month_label,
        "summary": summary,
        "year": year,
        "month": month,
    })


@login_required
def close_month(request, group_id):
    group = get_member_group_or_404(request.user, group_id)
    if not is_leader(request.user, group):
        raise PermissionDenied("Only the group leader can close a month.")
    if request.method != "POST":
        return redirect("mess:dashboard", group_id=group.pk)
    year, month = _month_from_request(request)
    today = date_cls.today()
    if (year, month) >= (today.year, today.month):
        return redirect(f"/mess/{group.pk}/dashboard/?year={year}&month={month}&close=not-ready")
    month_cycle = get_object_or_404(MonthCycle, group=group, year=year, month=month)
    month_cycle.is_closed = True
    month_cycle.closed_at = timezone.now()
    month_cycle.save(update_fields=["is_closed", "closed_at"])
    return redirect(f"/mess/{group.pk}/dashboard/?year={year}&month={month}&close=closed")


@login_required
def entry_form(request, group_id, user_id=None):
    group = get_member_group_or_404(request.user, group_id)
    target_user = get_object_or_404(User, pk=user_id) if user_id else request.user

    if request.method == "POST":
        form = DailyEntryForm(request.POST)
        if form.is_valid():
            try:
                record_daily_entry(
                    actor=request.user,
                    group=group,
                    target_user=target_user,
                    date=form.cleaned_data["date"],
                    lunch=Decimal("1") if form.cleaned_data["lunch"] else Decimal("0"),
                    dinner=Decimal("1") if form.cleaned_data["dinner"] else Decimal("0"),
                    cost=form.cleaned_data["cost"],
                )
                return redirect("mess:dashboard", group_id=group.pk)
            except PermissionDenied:
                form.add_error(None, "You don't have permission to edit this member's entry.")
    else:
        entry_date = date_cls.today()
        requested_date = request.GET.get("date")
        if requested_date:
            try:
                entry_date = date_cls.fromisoformat(requested_date)
            except ValueError:
                pass
        form = DailyEntryForm(initial={"date": entry_date})

    return render(
        request,
        "mess/entry_form.html",
        {"form": form, "group": group, "target_user": target_user},
    )


@login_required
def extra_meal_form(request, group_id, user_id):
    group = get_member_group_or_404(request.user, group_id)
    if not is_leader(request.user, group):
        raise PermissionDenied("Only the group leader can add extra meals.")
    target_user = get_object_or_404(
        User,
        pk=user_id,
        memberships__group=group,
        memberships__is_active=True,
    )

    if request.method == "POST":
        form = ExtraMealForm(request.POST)
        if form.is_valid():
            add_extra_meal(
                actor=request.user,
                group=group,
                target_user=target_user,
                date=form.cleaned_data["date"],
                meal_type=form.cleaned_data["meal_type"],
                quantity=form.cleaned_data["quantity"],
            )
            return redirect("mess:dashboard", group_id=group.pk)
    else:
        form = ExtraMealForm(initial={"date": date_cls.today()})

    return render(
        request,
        "mess/extra_meal_form.html",
        {"form": form, "group": group, "target_user": target_user},
    )


@login_required
def logs_view(request, group_id):
    group = get_member_group_or_404(request.user, group_id)
    if not can_view_logs(request.user, group):
        raise PermissionDenied("Only the group leader can view the audit log.")

    logs = group.logs.select_related("actor", "target_user")
    return render(request, "mess/logs.html", {"group": group, "logs": logs})