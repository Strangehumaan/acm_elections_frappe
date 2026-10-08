import frappe
from frappe.tests.utils import FrappeTestCase

from acm_elections.tasks import update_election_status
from acm_elections.tests.factories import make_election


def status_after_tick(**election_kwargs):
	election = make_election(**election_kwargs)
	update_election_status()
	return frappe.db.get_value("Election", election.name, "status")


class TestTasks(FrappeTestCase):
	def test_draft_opens(self):
		self.assertEqual(status_after_tick(status="Draft", start_offset_hours=-1, end_offset_hours=1), "Open")

	def test_draft_waits(self):
		self.assertEqual(status_after_tick(status="Draft", start_offset_hours=1, end_offset_hours=2), "Draft")

	def test_open_closes(self):
		self.assertEqual(status_after_tick(status="Open", start_offset_hours=-2, end_offset_hours=-0.02), "Closed")

	def test_stale_draft_closes(self):
		self.assertEqual(status_after_tick(status="Draft", start_offset_hours=-3, end_offset_hours=-1), "Closed")

	def test_closed_stays_closed(self):
		self.assertEqual(status_after_tick(status="Closed", start_offset_hours=-1, end_offset_hours=1), "Closed")
