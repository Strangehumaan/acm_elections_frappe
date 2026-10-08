import hashlib

import frappe
from frappe.tests.utils import FrappeTestCase

from acm_elections.tests.factories import make_election, make_voter
from acm_elections.tokens import find_voter, hash_token, issue_token


class TestTokens(FrappeTestCase):
	def setUp(self):
		election = make_election()
		self.voter = make_voter(election.name, f"{frappe.generate_hash(length=8)}@example.com")

	def test_hash_is_sha256(self):
		self.assertEqual(hash_token("abc"), hashlib.sha256(b"abc").hexdigest())

	def test_issue_and_find(self):
		token = issue_token(self.voter.name)
		self.assertEqual(find_voter(token), self.voter.name)
		stored, sent_at = frappe.db.get_value("Voter", self.voter.name, ["token_hash", "invite_sent_at"])
		self.assertNotEqual(stored, token)
		self.assertEqual(stored, hash_token(token))
		self.assertIsNotNone(sent_at)

	def test_reissue_kills_old_token(self):
		old = issue_token(self.voter.name)
		new = issue_token(self.voter.name)
		self.assertIsNone(find_voter(old))
		self.assertEqual(find_voter(new), self.voter.name)

	def test_find_none_and_empty(self):
		self.assertIsNone(find_voter(None))
		self.assertIsNone(find_voter(""))
		self.assertIsNone(find_voter("garbage"))
