from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from groups.models import Group


class MonthCycle(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="months")
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)

    # Cached so the dashboard doesn't re-aggregate every entry on every page
    # load. Kept in sync by signals in mess/signals.py whenever a DailyEntry
    # is saved or deleted.
    cached_total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cached_total_meals = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    cached_meal_rate = models.DecimalField(max_digits=8, decimal_places=4, default=0)

    class Meta:
        unique_together = ("group", "year", "month")
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"{self.group} — {self.year}-{self.month:02d}"

    def recalculate(self):
        """Recompute and cache totals from this cycle's DailyEntry rows."""
        from django.db.models import F, Sum

        agg = self.entries.aggregate(
            total_cost=Sum("cost"),
            total_meals=Sum(F("lunch") + F("dinner")),
        )
        total_cost = agg["total_cost"] or 0
        total_meals = agg["total_meals"] or 0

        self.cached_total_cost = total_cost
        self.cached_total_meals = total_meals
        self.cached_meal_rate = (total_cost / total_meals) if total_meals else 0
        self.save(update_fields=["cached_total_cost", "cached_total_meals", "cached_meal_rate"])

    def balance_for(self, user):
        """(cost, meals, due, balance) for one member in this cycle."""
        from django.db.models import F, Sum

        agg = self.entries.filter(user=user).aggregate(
            cost=Sum("cost"),
            meals=Sum(F("lunch") + F("dinner")),
        )
        cost = agg["cost"] or 0
        meals = agg["meals"] or 0
        due = meals * self.cached_meal_rate
        return {
            "cost": cost,
            "meals": meals,
            "due": due,
            "balance": cost - due,  # positive = gets money back, negative = owes
        }


class MonthlyEnrollment(models.Model):
    """A member opting into a given month's cycle."""

    month_cycle = models.ForeignKey(MonthCycle, on_delete=models.CASCADE, related_name="enrollments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("month_cycle", "user")

    def __str__(self):
        return f"{self.user} enrolled in {self.month_cycle}"


class DailyEntry(models.Model):
    month_cycle = models.ForeignKey(MonthCycle, on_delete=models.CASCADE, related_name="entries")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mess_entries"
    )
    date = models.DateField()
    # Decimal, not integer — supports half-meals and guest meals (your sheet
    # already showed values >1 in a single day).
    lunch = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    dinner = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("month_cycle", "user", "date")
        ordering = ["date"]

    def __str__(self):
        return f"{self.user} — {self.date}"

    @property
    def total_meals(self):
        return self.lunch + self.dinner