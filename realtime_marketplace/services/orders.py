"""Buyer/seller order reads and commands. Prices and actors come from Frappe."""

import frappe
from frappe import _

from realtime_marketplace.constants import (
	CLOSED_ORDER_STATUSES,
	INITIAL_ORDER_STATUS,
	INITIAL_PAYMENT_STATUS,
	ORDER_DOCTYPE,
	PRODUCT_DOCTYPE,
	UPDATABLE_ORDER_STATUSES,
)
from realtime_marketplace.permissions import require_login
from realtime_marketplace.realtime.order_events import publish_order_updated
from realtime_marketplace.serializers.orders import ORDER_FIELDS, serialize_order


def _get_orders_for_current_user(field):
	require_login()
	orders = frappe.get_all(
		ORDER_DOCTYPE,
		filters={field: frappe.session.user},
		fields=list(ORDER_FIELDS),
		order_by="creation desc",
		ignore_permissions=True,
	)
	return [serialize_order(order) for order in orders]


def get_buyer_orders():
	return _get_orders_for_current_user("buyer")


def get_seller_orders():
	return _get_orders_for_current_user("seller")


def place_order(product, quantity):
	require_login()
	quantity = frappe.utils.flt(quantity)
	if quantity <= 0:
		frappe.throw(_("Quantity must be greater than zero."))
	item = frappe.get_doc(PRODUCT_DOCTYPE, product)
	if not item.active:
		frappe.throw(_("This product is not available."))
	if item.stock_qty < quantity:
		frappe.throw(_("Insufficient stock."))
	if item.seller == frappe.session.user:
		frappe.throw(_("You cannot order your own product."))

	order = frappe.get_doc(
		{
			"doctype": ORDER_DOCTYPE,
			"buyer": frappe.session.user,
			"seller": item.seller,
			"product": item.name,
			"quantity": quantity,
			"unit_price": item.selling_price,
			"total_amount": item.selling_price * quantity,
			"order_status": INITIAL_ORDER_STATUS,
			"payment_status": INITIAL_PAYMENT_STATUS,
		}
	)
	# The DocType's after_insert publishes the new-order event for every creation path.
	order.insert(ignore_permissions=True)
	return {"order": order.name, "status": order.order_status}


def update_order_status(order_name, status):
	require_login()
	if status not in UPDATABLE_ORDER_STATUSES:
		frappe.throw(_("Invalid order status."))
	order = frappe.get_doc(ORDER_DOCTYPE, order_name)
	if order.seller != frappe.session.user:
		frappe.throw(_("Only the assigned seller can update this order."))
	if order.order_status in CLOSED_ORDER_STATUSES:
		frappe.throw(_("This order is already closed."))
	order.order_status = status
	order.save(ignore_permissions=True)
	publish_order_updated(order)
	return {"order": order.name, "status": order.order_status}
