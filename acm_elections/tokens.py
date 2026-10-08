"""One-time voting links.

The plaintext token only ever lives in the voter's email. The database keeps
its SHA-256 hash, so nobody reading the Voter table can rebuild a link.
"""

import hashlib
import secrets

import frappe
from frappe.utils import now_datetime


def hash_token(token: str) -> str:
	return hashlib.sha256(token.encode()).hexdigest()


def issue_token(voter: str) -> str:
	"""Give the voter a fresh token (replacing any older one) and return it."""
	token = secrets.token_urlsafe(32)
	frappe.db.set_value(
		"Voter", voter, {"token_hash": hash_token(token), "invite_sent_at": now_datetime()}
	)
	return token


def find_voter(token: str | None) -> str | None:
	"""Return the Voter name for this token, or None if it is missing or unknown."""
	if not token:
		return None
	return frappe.db.get_value("Voter", {"token_hash": hash_token(token)})
