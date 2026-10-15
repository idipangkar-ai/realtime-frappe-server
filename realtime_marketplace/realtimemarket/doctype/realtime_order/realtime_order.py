# Copyright (c) 2026, Dipangkar Hajong and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from realtime_marketplace.constants import PRODUCT_DOCTYPE
from realtime_marketplace.realtime.order_events import publish_new_order


class RealtimeOrder(Document):
	"""Keep creation invariants at the DocType lifecycle boundary."""

	def validate(self):
		if not self.is_new():
			return

		if frappe.session.user == "Guest":
			frappe.throw(_("Please log in to create an order."), frappe.PermissionError)

		if self.buyer != frappe.session.user and frappe.session.user != "Administrator":
			frappe.throw(_("You can only create orders for your own account."), frappe.PermissionError)

		product = frappe.get_doc(PRODUCT_DOCTYPE, self.product)
		if not product.active:
			frappe.throw(_("This product is not available."))

		if product.seller == self.buyer:
			frappe.throw(_("You cannot order your own product."))

		if product.stock_qty < self.quantity:
			frappe.throw(_("Insufficient stock."))

	def after_insert(self):
		publish_new_order(self)
