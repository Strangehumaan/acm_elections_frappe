import frappe
from frappe.tests.utils import FrappeTestCase

from acm_elections.results import get_ballot_register, get_results
from acm_elections.tests.factories import make_candidate, make_election, make_voter
from acm_elections.tokens import issue_token
from acm_elections.voting import submit_ballot


class TestResults(FrappeTestCase):
	def setUp(self):
		self.election = make_election(status="Draft", positions=["Chair", "Treasurer"])
		name = self.election.name
		self.a = make_candidate(name, "Chair", "Alpha").name
		self.b = make_candidate(name, "Chair", "Bravo").name
		self.c = make_candidate(name, "Chair", "Charlie").name
		self.t = make_candidate(name, "Treasurer", "Tango").name
		self.election.db_set("status", "Open")

	def vote(self, chair, voter_name="Voter"):
		voter = make_voter(self.election.name, f"{frappe.generate_hash(length=8)}@example.com", voter_name)
		submit_ballot(issue_token(voter.name), {"Chair": chair, "Treasurer": self.t})

	def chair(self):
		return get_results(self.election.name)["positions"][0]

	def close_and_pick(self, candidate):
		self.election.db_set("status", "Closed")
		self.election.reload()
		self.election.positions[0].tie_winner = candidate
		self.election.save()

	def test_counts_and_winner(self):
		self.vote(self.a)
		self.vote(self.a)
		self.vote(self.b)
		make_voter(self.election.name, f"{frappe.generate_hash(length=8)}@example.com")  # didn't vote

		results = get_results(self.election.name)
		self.assertEqual((results["voted"], results["total"]), (3, 4))
		chair = results["positions"][0]
		self.assertEqual(
			[(c["full_name"], c["votes"]) for c in chair["candidates"]],
			[("Alpha", 2), ("Bravo", 1), ("Charlie", 0)],
		)
		self.assertEqual(chair["winner"], self.a)
		self.assertEqual(chair["tied"], [])

	def test_tie_detected(self):
		self.vote(self.a)
		self.vote(self.b)
		self.assertEqual(self.chair()["tied"], [self.a, self.b])
		self.assertIsNone(self.chair()["winner"])

	def test_tie_winner_used(self):
		self.vote(self.a)
		self.vote(self.b)
		self.close_and_pick(self.b)
		self.assertEqual(self.chair()["winner"], self.b)

	def test_tie_winner_must_be_tied(self):
		self.vote(self.a)
		self.vote(self.b)

		self.election.reload()
		self.election.positions[0].tie_winner = self.b
		with self.assertRaises(frappe.ValidationError):
			self.election.save()  # still Open

		with self.assertRaises(frappe.ValidationError):
			self.close_and_pick(self.c)  # Charlie isn't in the tie

	def test_zero_votes_no_winner(self):
		for position in get_results(self.election.name)["positions"]:
			self.assertIsNone(position["winner"])
			self.assertEqual(position["tied"], [])
			self.assertTrue(all(c["votes"] == 0 for c in position["candidates"]))

	def test_ballot_register(self):
		self.vote(self.b, "Zoya")
		self.vote(self.a, "Aman")
		rows = get_ballot_register(self.election.name)
		self.assertEqual([r["voter_name"] for r in rows], ["Aman", "Zoya"])
		self.assertEqual(rows[0]["choices"], {"Chair": "Alpha", "Treasurer": "Tango"})
		self.assertIsNotNone(rows[0]["voted_at"])

	def test_election_results_report(self):
		from acm_elections.acm_elections.report.election_results.election_results import execute

		self.vote(self.a)
		self.vote(self.b)
		self.vote(self.b)
		columns, data = execute({"election": self.election.name})
		self.assertEqual(
			[c["fieldname"] for c in columns], ["position", "candidate", "votes", "result"]
		)
		self.assertEqual(
			[(r["position"], r["candidate"], r["votes"], r["result"]) for r in data],
			[
				("Chair", "Bravo", 2, "Winner"),
				("Chair", "Alpha", 1, ""),
				("Chair", "Charlie", 0, ""),
				("Treasurer", "Tango", 3, "Winner"),
			],
		)
