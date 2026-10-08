from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from acm_elections.demo import DEMO_TITLE, POSITIONS, create_demo


def counts(name):
	return (frappe.db.count("Candidate", {"election": name}), frappe.db.count("Voter", {"election": name}))


@patch("frappe.db.commit")  # keep the test inside its rollback
class TestDemo(FrappeTestCase):
	def test_demo_shape(self, _commit):
		name = create_demo()
		election = frappe.get_doc("Election", name)
		self.assertEqual(name, DEMO_TITLE)
		self.assertEqual(
			[p.position_name for p in election.positions],
			["Chair", "Vice Chair", "Member Chair", "Treasurer", "Secretary", "Web Master"],
		)
		self.assertEqual(POSITIONS, [p.position_name for p in election.positions])
		self.assertEqual(counts(name), (18, 5))
		for full_name in ("Vice Chair_1", "Web Master_3"):
			self.assertTrue(frappe.db.exists("Candidate", {"election": name, "full_name": full_name}))

	def test_demo_idempotent(self, _commit):
		first = create_demo()
		self.assertEqual(create_demo(), first)
		self.assertEqual(counts(first), (18, 5))


class TestQueuedLinks(FrappeTestCase):
	def test_queued_links_resolve_to_voters(self):
		from acm_elections.demo import queued_links
		from acm_elections.invitations import send_links
		from acm_elections.tests.factories import make_election, make_voter
		from acm_elections.tokens import find_voter

		frappe.db.set_value("Email Account", "_Test Email Account 1", "default_outgoing", 1)
		election = make_election()
		voter = make_voter(election.name, f"{frappe.generate_hash(length=8)}@example.com")
		send_links(election.name, "invite")

		links = queued_links(election.name)
		self.assertEqual(list(links), [voter.email])
		self.assertEqual(find_voter(links[voter.email].split("token=")[1]), voter.name)


test_dependencies = ["Email Account"]
