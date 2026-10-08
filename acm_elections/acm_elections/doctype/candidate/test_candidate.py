# Copyright (c) 2026, Mohammad Saad Nathani and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from acm_elections.tests.factories import make_candidate, make_election


class TestCandidate(FrappeTestCase):
	def test_position_must_exist(self):
		election = make_election(status="Draft")
		with self.assertRaises(frappe.ValidationError):
			make_candidate(election.name, "President")

	def test_candidate_allowed_in_draft(self):
		election = make_election(status="Draft")
		candidate = make_candidate(election.name, "Chair", "Chair_1")
		self.assertEqual(candidate.position, "Chair")

	def test_candidate_frozen_after_draft(self):
		election = make_election(status="Draft")
		candidate = make_candidate(election.name, "Chair")
		election.db_set("status", "Open")

		with self.assertRaises(frappe.ValidationError):
			make_candidate(election.name, "Chair", "Late Entry")

		candidate.reload()
		candidate.position = "Treasurer"
		with self.assertRaises(frappe.ValidationError):
			candidate.save()
