from django.http import Http404
from django.shortcuts import get_object_or_404

from .models import Group
from .permissions import is_member


def get_member_group_or_404(user, group_id):
    """
    404 (not 403) for non-members — a group's existence isn't revealed to
    people outside it, which is what "can't see others' group activity"
    actually requires.
    """
    group = get_object_or_404(Group, pk=group_id)
    if not is_member(user, group):
        raise Http404("Group not found.")
    return group