"""Authentication guards for custom marketplace operations."""

import frappe
from frappe import _


def require_login():
	if frappe.session.user == "Guest":
		frappe.throw(_("Please log in to continue."), frappe.PermissionError)
