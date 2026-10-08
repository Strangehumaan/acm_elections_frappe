import frappe
from frappe.tests.utils import FrappeTestCase

from acm_elections.tests.factories import make_candidate, make_election, make_voter
from acm_elections.tokens import issue_token
from acm_elections.voting import submit_ballot


class TestPrintFormats(FrappeTestCase):
	def setUp(self):
		self.election = make_election(status="Draft", positions=["Chair", "Treasurer"])
		name = self.election.name
		self.a = make_candidate(name, "Chair", "Alpha").name
		self.b = make_candidate(name, "Chair", "Bravo").name
		self.t = make_candidate(name, "Treasurer", "Tango").name
		self.election.db_set("status", "Open")

	def vote(self, chair, voter_name):
		voter = make_voter(self.election.name, f"{frappe.generate_hash(length=8)}@example.com", voter_name)
		submit_ballot(issue_token(voter.name), {"Chair": chair, "Treasurer": self.t})

	def render(self, print_format):
		return frappe.get_print("Election", self.election.name, print_format=print_format)

	def test_results_summary_winner_and_turnout(self):
		self.vote(self.a, "Aman")
		self.vote(self.a, "Zoya")
		html = self.render("Results Summary")
		self.assertIn("Turnout: 2 of 2 voted (100.0%)", html)
		self.assertIn("Alpha", html)
		self.assertIn("Winner", html)

	def test_results_summary_tie_wording(self):
		self.vote(self.a, "Aman")
		self.vote(self.b, "Zoya")
		self.assertIn("TIE — unresolved", self.render("Results Summary"))

		self.election.db_set("status", "Closed")
		self.election.reload()
		self.election.positions[0].tie_winner = self.b
		self.election.save()
		self.assertIn("TIE — winner chosen by committee: Bravo", self.render("Results Summary"))

	def test_results_summary_no_votes(self):
		self.assertIn("No votes", self.render("Results Summary"))

	def test_ballot_register(self):
		self.vote(self.b, "Zoya")
		html = self.render("Ballot Register")
		self.assertIn("Confidential — committee only", html)
		self.assertIn("Zoya", html)
		self.assertIn("Bravo", html)
		self.assertIn("Tango", html)
