from datetime import date

from django.test import TestCase

from accounts.models import User
from groups.models import Group, GroupMembership

from .models import DailyEntry, MonthCycle


class MonthlyLifecycleTests(TestCase):
	def setUp(self):
		self.leader = User.objects.create_user(
			username="lifecycle-leader",
			email="lifecycle-leader@example.com",
			password="test-pass-12345",
		)
		self.member = User.objects.create_user(
			username="lifecycle-member",
			email="lifecycle-member@example.com",
			password="test-pass-12345",
		)
		self.group = Group.objects.create(name="Lifecycle Group", created_by=self.leader)
		GroupMembership.objects.create(
			group=self.group, user=self.leader, role=GroupMembership.Role.LEADER
		)
		GroupMembership.objects.create(
			group=self.group, user=self.member, role=GroupMembership.Role.MEMBER
		)
		self.client.force_login(self.leader)

	def test_malformed_month_falls_back_to_current_dashboard(self):
		response = self.client.get(
			f"/mess/{self.group.pk}/dashboard/?year=bad&month=bad"
		)
		self.assertEqual(response.status_code, 200)

	def test_close_locks_entries(self):
		cycle = MonthCycle.objects.create(group=self.group, year=2026, month=8)
		response = self.client.post(
			f"/mess/{self.group.pk}/close-month/", {"year": 2026, "month": 8}
		)
		self.assertEqual(response.status_code, 302)
		cycle.refresh_from_db()
		self.assertTrue(cycle.is_closed)

		entry_response = self.client.post(
			f"/mess/{self.group.pk}/entry/{self.member.pk}/",
			{"date": "2026-08-12", "lunch": "on", "cost": "10"},
		)
		self.assertEqual(entry_response.status_code, 200)
		self.assertFalse(DailyEntry.objects.filter(month_cycle=cycle).exists())

	def test_current_month_cannot_be_closed(self):
		response = self.client.post(
			f"/mess/{self.group.pk}/close-month/", {"year": 2026, "month": 9}
		)
		self.assertIn("not-ready", response.url)

	def test_monthly_details_and_personal_calculation_are_available(self):
		response = self.client.get(
			f"/mess/{self.group.pk}/details/?year=2026&month=8"
		)
		self.assertEqual(response.status_code, 200)
		response = self.client.get(
			f"/mess/{self.group.pk}/my-calculation/?year=2026&month=8"
		)
		self.assertEqual(response.status_code, 200)
