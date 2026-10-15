"""Catalog reads for authenticated marketplace users."""

import frappe

from realtime_marketplace.constants import PRODUCT_DOCTYPE
from realtime_marketplace.permissions import require_login


def get_active_products():
	require_login()
	return frappe.get_all(
		PRODUCT_DOCTYPE,
		filters={"active": 1, "stock_qty": [">", 0]},
		fields=["name", "product_name", "category", "seller", "selling_price", "unit", "stock_qty"],
		order_by="modified desc",
		ignore_permissions=True,
	)
