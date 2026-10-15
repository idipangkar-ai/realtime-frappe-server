"""Keep order response fields consistent across buyer and seller views."""

import frappe

from realtime_marketplace.constants import PRODUCT_DOCTYPE

ORDER_FIELDS = (
	"name",
	"buyer",
	"seller",
	"product",
	"quantity",
	"unit_price",
	"total_amount",
	"order_status",
	"payment_status",
	"creation",
	"modified",
)


def serialize_order(order):
	product_name = frappe.db.get_value(PRODUCT_DOCTYPE, order.product, "product_name")
	return {
		"name": order.name,
		"buyer": order.buyer,
		"seller": order.seller,
		"product": order.product,
		"product_name": product_name or order.product,
		"quantity": order.quantity,
		"unit_price": order.unit_price,
		"total_amount": order.total_amount,
		"order_status": order.order_status,
		"payment_status": order.payment_status,
		"creation": order.creation,
		"modified": order.modified,
	}
