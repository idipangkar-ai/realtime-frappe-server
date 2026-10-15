"""Authenticated identity and account summary queries."""

import frappe

from realtime_marketplace.constants import ORDER_DOCTYPE, PENDING_ORDER_STATUSES, PRODUCT_DOCTYPE
from realtime_marketplace.permissions import require_login


def get_dashboard_context():
	require_login()
	user = frappe.session.user
	user_doc = frappe.get_cached_doc("User", user)
	seller_order_names = frappe.get_all(
		ORDER_DOCTYPE,
		filters={"seller": user},
		pluck="name",
		ignore_permissions=True,
	)
	buyer_order_names = frappe.get_all(
		ORDER_DOCTYPE,
		filters={"buyer": user},
		pluck="name",
		ignore_permissions=True,
	)
	order_names = list(set(seller_order_names + buyer_order_names))
	return {
		"user": {
			"name": user_doc.name,
			"full_name": user_doc.full_name,
			"email": user_doc.email,
			"user_type": user_doc.user_type,
			"roles": frappe.get_roles(user),
		},
		"summary": {
			"total_products": frappe.db.count(PRODUCT_DOCTYPE, {"seller": user}),
			"active_products": frappe.db.count(PRODUCT_DOCTYPE, {"seller": user, "active": 1}),
			"total_orders": len(order_names),
			"pending_orders": frappe.db.count(
				ORDER_DOCTYPE,
				{"name": ["in", order_names], "order_status": ["in", list(PENDING_ORDER_STATUSES)]},
			)
			if order_names
			else 0,
		},
	}
