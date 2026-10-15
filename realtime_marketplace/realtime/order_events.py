"""Publish only after commit, to the same recipients and payloads as before."""

import frappe

from realtime_marketplace.constants import NEW_ORDER_EVENT, ORDER_UPDATED_EVENT, PRODUCT_DOCTYPE


def publish_new_order(order):
	product_name = frappe.db.get_value(PRODUCT_DOCTYPE, order.product, "product_name")
	frappe.publish_realtime(
		NEW_ORDER_EVENT,
		{
			"order": order.name,
			"product": product_name or order.product,
			"quantity": order.quantity,
			"total_amount": order.total_amount,
		},
		user=order.seller,
		after_commit=True,
	)


def publish_order_updated(order):
	product_name = frappe.db.get_value(PRODUCT_DOCTYPE, order.product, "product_name")
	frappe.publish_realtime(
		ORDER_UPDATED_EVENT,
		{
			"order": order.name,
			"status": order.order_status,
			"product": product_name or order.product,
		},
		user=order.buyer,
		after_commit=True,
	)
