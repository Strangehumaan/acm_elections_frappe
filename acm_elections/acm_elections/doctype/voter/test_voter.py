# Copyright (c) 2026, Mohammad Saad Nathani and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from acm_elections.tests.factories import make_election, make_voter


class TestVoter(FrappeTestCase):
	def test_email_normalised_and_unique(self):
		election = make_election()
		voter = make_voter(election.name, " Saad@X.com ")
		self.assertEqual(voter.email, "saad@x.com")

		with self.assertRaises(frappe.ValidationError):
			make_voter(election.name, "saad@x.com")

		other = make_election()
		self.assertEqual(make_voter(other.name, "saad@x.com").email, "saad@x.com")
