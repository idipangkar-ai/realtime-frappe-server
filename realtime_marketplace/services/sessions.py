"""Authenticated mobile bootstrap; password verification stays in Frappe."""

import frappe
from frappe.sessions import get_csrf_token

from realtime_marketplace.permissions import require_login
from realtime_marketplace.services.accounts import get_dashboard_context


def get_mobile_session():
	require_login()
	context = get_dashboard_context()
	return {"sid": frappe.session.sid, "csrf_token": get_csrf_token(), **context}
