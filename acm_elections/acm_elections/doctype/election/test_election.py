# Copyright (c) 2026, Mohammad Saad Nathani and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from acm_elections.tests.factories import make_election


class TestElection(FrappeTestCase):
	def test_end_must_be_after_start(self):
		with self.assertRaises(frappe.ValidationError):
			make_election(start_offset_hours=-1, end_offset_hours=-2)

	def test_needs_a_position(self):
		with self.assertRaises(frappe.ValidationError):
			make_election(positions=[])

	def test_position_names_unique(self):
		with self.assertRaises(frappe.ValidationError):
			make_election(positions=["Chair", "chair "])

	def test_positions_editable_in_draft(self):
		election = make_election(status="Draft")
		election.append("positions", {"position_name": "Secretary"})
		election.save()
		self.assertEqual(len(election.positions), 3)

	def test_positions_frozen_after_draft(self):
		election = make_election(status="Open")

		election.reload()
		election.append("positions", {"position_name": "Secretary"})
		with self.assertRaises(frappe.ValidationError):
			election.save()

		election.reload()
		election.positions[0].position_name = "President"
		with self.assertRaises(frappe.ValidationError):
			election.save()

	def test_new_election_starts_draft(self):
		election = frappe.get_doc(
			{
				"doctype": "Election",
				"title": f"Sneaky {frappe.generate_hash(length=8)}",
				"status": "Open",
				"start_time": "2026-01-01 10:00:00",
				"end_time": "2026-01-02 10:00:00",
				"positions": [{"position_name": "Chair"}],
			}
		).insert()
		self.assertEqual(election.status, "Draft")
