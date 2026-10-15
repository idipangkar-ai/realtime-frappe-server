"""Account HTTP endpoints. Business queries live in services/accounts.py."""

import frappe

from realtime_marketplace.services import accounts


@frappe.whitelist()
def get_dashboard_context():
	return accounts.get_dashboard_context()
