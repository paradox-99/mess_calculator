from .models import GroupMembership


def get_membership(user, group):
    return GroupMembership.objects.filter(group=group, user=user, is_active=True).first()


def is_member(user, group):
    return get_membership(user, group) is not None


def is_leader(user, group):
    membership = get_membership(user, group)
    return membership is not None and membership.role == GroupMembership.Role.LEADER


def can_edit_entry(actor, group, target_user):
    """Leader can edit anyone's entry in their group; a member can edit only their own."""
    membership = get_membership(actor, group)
    if membership is None:
        return False
    if membership.role == GroupMembership.Role.LEADER:
        return True
    return actor.pk == target_user.pk


def can_view_logs(user, group):
    """Only the leader sees the audit trail."""
    return is_leader(user, group)