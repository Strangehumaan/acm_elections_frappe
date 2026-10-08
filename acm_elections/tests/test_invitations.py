import email

import frappe
from frappe.tests.utils import FrappeTestCase

from acm_elections.invitations import send_links
from acm_elections.tests.factories import make_election, make_voter
from acm_elections.tokens import issue_token

test_dependencies = ["Email Account"]  # Frappe's test SMTP accounts, so sendmail can queue


def queued_text(voter):
	"""Decoded text of the queued email for this voter."""
	raw = frappe.db.get_value("Email Queue", {"reference_doctype": "Voter", "reference_name": voter}, "message")
	parts = email.message_from_string(raw).walk()
	return "".join(p.get_payload(decode=True).decode() for p in parts if not p.is_multipart())


class TestInvitations(FrappeTestCase):
	def setUp(self):
		frappe.db.set_value("Email Account", "_Test Email Account 1", "default_outgoing", 1)
		self.election = make_election(status="Open")
		self.voters = [
			make_voter(self.election.name, f"{frappe.generate_hash(length=8)}@example.com", f"Voter {i}").name
			for i in range(3)
		]

	def hashes(self):
		return {v: frappe.db.get_value("Voter", v, "token_hash") for v in self.voters}

	def test_invite_targets_uninvited(self):
		issue_token(self.voters[0])
		self.assertEqual(send_links(self.election.name, "invite"), 2)
		for voter in self.voters[1:]:
			self.assertIn("/vote?token=", queued_text(voter))
		self.assertFalse(frappe.db.exists("Email Queue", {"reference_name": self.voters[0]}))

	def test_reminder_targets_invited_nonvoters(self):
		for voter in self.voters:
			issue_token(voter)
		frappe.db.set_value("Voter", self.voters[0], "has_voted", 1)
		before = self.hashes()

		self.assertEqual(send_links(self.election.name, "reminder"), 2)
		after = self.hashes()
		self.assertEqual(before[self.voters[0]], after[self.voters[0]])
		for voter in self.voters[1:]:
			self.assertNotEqual(before[voter], after[voter])
			self.assertIn("Reminder", queued_text(voter))

	def test_closed_election_blocks_sending(self):
		self.election.db_set("status", "Closed")
		with self.assertRaises(frappe.ValidationError):
			send_links(self.election.name, "invite")

	def test_close_now(self):
		self.election.reload()
		self.election.close_now()
		self.assertEqual(frappe.db.get_value("Election", self.election.name, "status"), "Closed")

		draft = make_election(status="Draft")
		with self.assertRaises(frappe.ValidationError):
			draft.close_now()

	def test_turnout(self):
		frappe.db.set_value("Voter", self.voters[0], "has_voted", 1)
		self.assertEqual(self.election.get_turnout(), {"voted": 1, "total": 3})

	def test_links_redacted_after_send(self):
		send_links(self.election.name, "invite")
		flags = frappe.get_all(
			"Email Queue",
			{"reference_doctype": "Voter", "reference_name": ("in", self.voters)},
			pluck="redact_message_after_send",
		)
		self.assertEqual(flags, [1, 1, 1])
