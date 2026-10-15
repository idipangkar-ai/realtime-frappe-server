"""Mobile session endpoint; authentication remains Frappe's standard login."""

import frappe

from realtime_marketplace.services.sessions import get_mobile_session


@frappe.whitelist(methods=["GET"])
def get_session():
	return get_mobile_session()
