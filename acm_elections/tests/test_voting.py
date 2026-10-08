import json

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, now_datetime

from acm_elections.tests.factories import make_candidate, make_election, make_voter
from acm_elections.tokens import issue_token
from acm_elections.voting import (
	ALREADY_VOTED,
	INVALID_LINK,
	NOT_OPEN,
	THANK_YOU,
	VotingError,
	get_ballot_context,
	submit_ballot,
)


class TestVoting(FrappeTestCase):
	def setUp(self):
		self.election = make_election(status="Draft", positions=["Chair", "Treasurer"])
		name = self.election.name
		self.chair_a = make_candidate(name, "Chair", "Chair A").name
		self.chair_b = make_candidate(name, "Chair", "Chair B").name
		self.treasurer_a = make_candidate(name, "Treasurer", "Treasurer A").name
		self.treasurer_b = make_candidate(name, "Treasurer", "Treasurer B").name
		self.election.db_set("status", "Open")
		self.voter = make_voter(name, f"{frappe.generate_hash(length=8)}@example.com", "Asha")
		self.token = issue_token(self.voter.name)
		self.choices = {"Chair": self.chair_a, "Treasurer": self.treasurer_b}

	def ballot_count(self):
		return frappe.db.count("Ballot", {"voter": self.voter.name})

	def assert_rejected(self, choices):
		with self.assertRaises(VotingError):
			submit_ballot(self.token, choices)
		self.assertEqual(self.ballot_count(), 0)

	def test_context_ok(self):
		context = get_ballot_context(self.token)
		self.assertIsNone(context["error"])
		self.assertEqual(context["voter_name"], "Asha")
		self.assertEqual([p["position"] for p in context["positions"]], ["Chair", "Treasurer"])
		chair_names = [c["full_name"] for c in context["positions"][0]["candidates"]]
		self.assertEqual(chair_names, ["Chair A", "Chair B"])

	def test_context_missing_or_bad_token(self):
		for token in (None, "", "nope"):
			self.assertEqual(get_ballot_context(token)["error"], INVALID_LINK)

	def test_context_not_open(self):
		self.election.db_set("status", "Draft")
		self.assertEqual(get_ballot_context(self.token)["error"], NOT_OPEN)

		now = now_datetime()
		self.election.db_set(
			{"status": "Open", "start_time": add_to_date(now, hours=-3), "end_time": add_to_date(now, hours=-1)}
		)
		self.assertEqual(get_ballot_context(self.token)["error"], NOT_OPEN)

	def test_submit_happy_path(self):
		self.assertEqual(submit_ballot(self.token, self.choices), {"message": THANK_YOU})
		self.assertEqual(self.ballot_count(), 1)
		ballot = frappe.get_doc("Ballot", {"voter": self.voter.name})
		self.assertEqual({c.position: c.candidate for c in ballot.choices}, self.choices)
		self.voter.reload()
		self.assertEqual(self.voter.has_voted, 1)
		self.assertIsNotNone(self.voter.voted_at)

	def test_second_submit_rejected(self):
		submit_ballot(self.token, self.choices)
		with self.assertRaises(VotingError) as caught:
			submit_ballot(self.token, self.choices)
		self.assertIn(ALREADY_VOTED, str(caught.exception))
		self.assertEqual(self.ballot_count(), 1)
		self.assertEqual(get_ballot_context(self.token)["error"], ALREADY_VOTED)

	def test_missing_position(self):
		self.assert_rejected({"Chair": self.chair_a})

	def test_extra_position(self):
		self.assert_rejected({**self.choices, "Secretary": self.chair_b})

	def test_wrong_position_candidate(self):
		self.assert_rejected({"Chair": self.treasurer_a, "Treasurer": self.chair_a})

	def test_candidate_from_other_election(self):
		other = make_election(status="Draft", positions=["Chair", "Treasurer"])
		outsider = make_candidate(other.name, "Chair", "Outsider").name
		self.assert_rejected({"Chair": outsider, "Treasurer": self.treasurer_a})

	def test_choices_as_json_string(self):
		submit_ballot(self.token, json.dumps(self.choices))
		self.assertEqual(self.ballot_count(), 1)

	def test_malformed_choices(self):
		self.assert_rejected("not json")
		self.assert_rejected("[1, 2]")

	def test_ballot_is_read_only(self):
		submit_ballot(self.token, self.choices)
		ballot = frappe.get_doc("Ballot", {"voter": self.voter.name})
		ballot.submitted_at = add_to_date(now_datetime(), days=-1)
		with self.assertRaises(frappe.ValidationError):
			ballot.save(ignore_permissions=True)
