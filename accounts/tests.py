from django.test import TestCase

from .views import SignUpForm


class SignupFormTests(TestCase):
	def test_signup_includes_names(self):
		self.assertEqual(
			list(SignUpForm().fields),
			["username", "first_name", "last_name", "email", "password1", "password2"],
		)
