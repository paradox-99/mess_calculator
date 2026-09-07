from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import DailyEntry


@receiver(post_save, sender=DailyEntry)
@receiver(post_delete, sender=DailyEntry)
def recalculate_month_cycle(sender, instance, **kwargs):
    """Keep MonthCycle's cached totals in sync whenever an entry changes."""
    instance.month_cycle.recalculate()