"""Catalog HTTP endpoints. Product queries live in services/products.py."""

import frappe

from realtime_marketplace.services import products


@frappe.whitelist()
def get_active_products():
	return products.get_active_products()
