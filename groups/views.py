from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.shortcuts import redirect, render

from .forms import (
    GroupCreateForm,
    GroupJoinForm,
    LeadershipTransferForm,
    MemberUsernameForm,
)
from .models import Group, GroupMembership


@login_required
def group_list(request):
    memberships = (
        GroupMembership.objects.filter(user=request.user, is_active=True)
        .select_related("group")
    )
    existing_membership = memberships.first()
    if existing_membership:
        return redirect("mess:dashboard", group_id=existing_membership.group_id)
    return render(request, "groups/group_list.html", {"memberships": memberships})


@login_required
def group_create(request):
    existing_membership = (
        GroupMembership.objects.filter(user=request.user, is_active=True)
        .select_related("group")
        .first()
    )
    if existing_membership:
        return redirect("mess:dashboard", group_id=existing_membership.group_id)

    if request.method == "POST":
        form = GroupCreateForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            GroupMembership.objects.create(
                group=group, user=request.user, role=GroupMembership.Role.LEADER
            )
            return redirect("mess:dashboard", group_id=group.pk)
    else:
        form = GroupCreateForm()
    return render(request, "groups/group_create.html", {"form": form})


@login_required
def group_join(request):
    existing_membership = (
        GroupMembership.objects.filter(user=request.user, is_active=True)
        .select_related("group")
        .first()
    )
    if existing_membership:
        return redirect("mess:dashboard", group_id=existing_membership.group_id)

    if request.method == "POST":
        form = GroupJoinForm(request.POST)
        if form.is_valid():
            group = form.cleaned_data["group"]
            GroupMembership.objects.get_or_create(
                group=group,
                user=request.user,
                defaults={"role": GroupMembership.Role.MEMBER},
            )
            return redirect("mess:dashboard", group_id=group.pk)
    else:
        form = GroupJoinForm()
    return render(request, "groups/group_join.html", {"form": form})


@login_required
def add_member(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    membership = GroupMembership.objects.filter(
        group=group, user=request.user, is_active=True
    ).first()
    if membership is None or membership.role != GroupMembership.Role.LEADER:
        raise PermissionDenied

    if request.method == "POST":
        form = MemberUsernameForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["username"]
            active_membership = GroupMembership.objects.filter(
                user=user, is_active=True
            ).first()
            if active_membership:
                if active_membership.group_id == group.pk:
                    form.add_error("username", "This user is already a member of this group.")
                else:
                    form.add_error("username", "This user is already in another group.")
            else:
                group_membership, _ = GroupMembership.objects.get_or_create(
                    group=group,
                    user=user,
                    defaults={"role": GroupMembership.Role.MEMBER},
                )
                group_membership.is_active = True
                group_membership.left_at = None
                group_membership.save(update_fields=["is_active", "left_at"])
                return redirect("mess:dashboard", group_id=group.pk)
    else:
        form = MemberUsernameForm()
    return render(request, "groups/member_form.html", {
        "form": form,
        "group": group,
        "action": "Add member",
    })


@login_required
def remove_member(request, group_id, user_id):
    group = get_object_or_404(Group, pk=group_id)
    leader_membership = GroupMembership.objects.filter(
        group=group, user=request.user, role=GroupMembership.Role.LEADER, is_active=True
    ).first()
    if leader_membership is None:
        raise PermissionDenied
    if request.method != "POST":
        return redirect("mess:dashboard", group_id=group.pk)

    member = GroupMembership.objects.filter(
        group=group, user_id=user_id, is_active=True
    ).first()
    if member and member.role != GroupMembership.Role.LEADER:
        member.is_active = False
        member.left_at = timezone.now()
        member.save(update_fields=["is_active", "left_at"])
    return redirect("mess:dashboard", group_id=group.pk)


@login_required
def transfer_leadership(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    leader_membership = GroupMembership.objects.filter(
        group=group, user=request.user, role=GroupMembership.Role.LEADER, is_active=True
    ).first()
    if leader_membership is None:
        raise PermissionDenied

    if request.method == "POST":
        form = LeadershipTransferForm(request.POST, group=group)
        if form.is_valid():
            new_leader = form.cleaned_data["member"]
            with transaction.atomic():
                current_membership = GroupMembership.objects.select_for_update().get(
                    group=group, user=request.user
                )
                new_membership = GroupMembership.objects.select_for_update().get(
                    group=group, user=new_leader, is_active=True
                )
                current_membership.role = GroupMembership.Role.MEMBER
                new_membership.role = GroupMembership.Role.LEADER
                current_membership.save(update_fields=["role"])
                new_membership.save(update_fields=["role"])
            return redirect("mess:dashboard", group_id=group.pk)
    else:
        form = LeadershipTransferForm(group=group)
    return render(request, "groups/transfer_leadership.html", {
        "form": form,
        "group": group,
    })