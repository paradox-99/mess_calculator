from django.contrib import admin

from .models import DailyEntry, MonthCycle, MonthlyEnrollment


class DailyEntryInline(admin.TabularInline):
    model = DailyEntry
    extra = 0


@admin.register(MonthCycle)
class MonthCycleAdmin(admin.ModelAdmin):
    list_display = (
        "group", "year", "month", "is_closed",
        "cached_total_cost", "cached_total_meals", "cached_meal_rate",
    )
    list_filter = ("group", "is_closed")
    readonly_fields = ("cached_total_cost", "cached_total_meals", "cached_meal_rate")
    inlines = [DailyEntryInline]


@admin.register(MonthlyEnrollment)
class MonthlyEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "month_cycle", "enrolled_at")


@admin.register(DailyEntry)
class DailyEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "month_cycle", "date", "lunch", "dinner", "cost")
    list_filter = ("month_cycle__group", "month_cycle")
    date_hierarchy = "date"