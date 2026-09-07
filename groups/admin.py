from django.contrib import admin

from .models import Group, GroupMembership


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 0


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "invite_code", "created_by", "created_at")
    search_fields = ("name", "invite_code")
    inlines = [GroupMembershipInline]


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "group", "role", "is_active", "joined_at")
    list_filter = ("role", "is_active", "group")