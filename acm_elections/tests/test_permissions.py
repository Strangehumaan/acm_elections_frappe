import os
import tempfile
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from acm_elections.results import get_ballot_register, get_results
from acm_elections.tests.factories import make_candidate, make_election, make_voter
from acm_elections.tokens import issue_token
from acm_elections.voting import submit_ballot

ADMIN = "election.admin@example.com"
OUTSIDER = "not.an.admin@example.com"


def make_user(email, roles):
	if not frappe.db.exists("User", email):
		user = frappe.get_doc({"doctype": "User", "email": email, "first_name": email.split("@")[0]})
		user.flags.no_welcome_mail = True
		user.insert(ignore_permissions=True)
		user.add_roles(*roles)
	return email


class TestPermissions(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		make_user(ADMIN, ["Election Admin"])
		make_user(OUTSIDER, [])
		self.election = make_election(status="Draft", positions=["Chair"])
		self.chair = make_candidate(self.election.name, "Chair", "Alpha").name
		self.election.db_set("status", "Open")
		self.voter = make_voter(self.election.name, f"{frappe.generate_hash(length=8)}@example.com")

	def tearDown(self):
		frappe.set_user("Administrator")

	def vote(self):
		submit_ballot(issue_token(self.voter.name), {"Chair": self.chair})
		return frappe.db.get_value("Ballot", {"voter": self.voter.name})

	def test_election_admin_can_only_read_ballots(self):
		frappe.set_user(ADMIN)
		self.assertTrue(frappe.has_permission("Ballot", "read"))
		for ptype in ("create", "write", "delete"):
			self.assertFalse(frappe.has_permission("Ballot", ptype), ptype)
		self.assertFalse(frappe.get_meta("Ballot").allow_rename)

	def test_ballot_cannot_be_deleted(self):
		ballot = self.vote()
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("Ballot", ballot)

	def test_one_ballot_per_voter_in_database(self):
		self.vote()
		duplicate = frappe.get_doc(
			{
				"doctype": "Ballot",
				"election": self.election.name,
				"voter": self.voter.name,
				"choices": [{"position": "Chair", "candidate": self.chair}],
			}
		)
		with self.assertRaises(frappe.UniqueValidationError):
			duplicate.insert(ignore_permissions=True)

	def test_results_need_election_permission(self):
		frappe.set_user(OUTSIDER)
		with self.assertRaises(frappe.PermissionError):
			get_results(self.election.name)
		with self.assertRaises(frappe.PermissionError):
			get_ballot_register(self.election.name)

		frappe.set_user(ADMIN)
		self.assertEqual(get_results(self.election.name)["total"], 1)
		self.assertEqual(get_ballot_register(self.election.name), [])

	def test_election_admin_can_import_voters(self):
		self.assertTrue(frappe.get_meta("Voter").allow_import)
		frappe.set_user(ADMIN)
		self.assertTrue(frappe.has_permission("Voter", "import"))
		self.assertTrue(frappe.has_permission("Data Import", "create"))

	@patch("frappe.db.rollback")
	@patch("frappe.db.commit")
	def test_voter_csv_import(self, _commit, _rollback):
		from frappe.core.doctype.data_import.importer import Importer

		csv = f"Election,Full Name,Email\n{self.election.name},Saad, Saad@X.com \n"
		with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
			f.write(csv)
		# Its own (unsaved) Data Import name, so import logs from other runs can't mark rows as done.
		data_import = frappe.new_doc("Data Import")
		data_import.name = f"test-{frappe.generate_hash(length=10)}"
		data_import.import_type = "Insert New Records"
		try:
			Importer("Voter", data_import=data_import, file_path=f.name, console=True).import_data()
		finally:
			os.unlink(f.name)
			# the importer writes logs; another test's commit would otherwise persist them
			frappe.db.delete("Data Import Log", {"data_import": data_import.name})
		self.assertTrue(frappe.db.exists("Voter", {"election": self.election.name, "email": "saad@x.com"}))
