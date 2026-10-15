"""Order endpoints plus compatibility routes used by existing mobile/web clients."""

import frappe

from realtime_marketplace.permissions import require_login as _require_login
from realtime_marketplace.serializers.orders import serialize_order as _serialize_order
from realtime_marketplace.services import accounts, orders, products


@frappe.whitelist()
def get_dashboard_context():
	"""Compatibility route; new clients may use api.accounts.get_dashboard_context."""
	return accounts.get_dashboard_context()


@frappe.whitelist()
def get_active_products():
	"""Compatibility route; new clients may use api.products.get_active_products."""
	return products.get_active_products()


@frappe.whitelist()
def get_buyer_orders():
	return orders.get_buyer_orders()


@frappe.whitelist()
def get_seller_orders():
	return orders.get_seller_orders()


@frappe.whitelist()
def place_order(product, quantity):
	return orders.place_order(product, quantity)


@frappe.whitelist()
def update_order_status(order_name, status):
	return orders.update_order_status(order_name, status)
