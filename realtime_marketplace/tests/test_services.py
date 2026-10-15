"""Regression checks for the extracted custom services and public API contracts."""

import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import Mock, patch

import frappe

from realtime_marketplace import permissions
from realtime_marketplace.api import accounts as account_api
from realtime_marketplace.api import mobile as mobile_api
from realtime_marketplace.api import orders as order_api
from realtime_marketplace.api import products as product_api
from realtime_marketplace.realtime import order_events
from realtime_marketplace.realtimemarket.doctype.realtime_order.realtime_order import RealtimeOrder
from realtime_marketplace.services import accounts, orders, products, sessions


class MarketplaceServiceTests(unittest.TestCase):
	def setUp(self):
		self.stack = ExitStack()
		self.addCleanup(self.stack.close)
		self.session = SimpleNamespace(user="buyer@example.test", sid="test-session")
		self.db = SimpleNamespace(get_value=Mock(return_value="Test Product"), count=Mock(return_value=0))
		self.stack.enter_context(patch.object(frappe, "session", self.session, create=True))
		self.stack.enter_context(
			patch.object(frappe, "local", SimpleNamespace(request=None, flags=SimpleNamespace(in_test=False)))
		)
		self.stack.enter_context(patch.object(frappe, "db", self.db, create=True))
		self.stack.enter_context(patch.object(frappe, "throw", side_effect=self.throw))
		self.stack.enter_context(patch.object(permissions, "_", lambda value: value))
		self.stack.enter_context(patch.object(orders, "_", lambda value: value))

	@staticmethod
	def throw(message, exception=ValueError):
		raise exception(message)

	def test_guest_cannot_access_catalog_or_orders(self):
		self.session.user = "Guest"
		for operation in (products.get_active_products, orders.get_buyer_orders, orders.get_seller_orders):
			with self.subTest(operation=operation.__name__), self.assertRaises(frappe.PermissionError):
				operation()

	def test_product_query_keeps_active_and_stock_filters(self):
		with patch.object(frappe, "get_all", return_value=[]) as query:
			self.assertEqual(products.get_active_products(), [])
		self.assertEqual(query.call_args.kwargs["filters"], {"active": 1, "stock_qty": [">", 0]})

	def test_buyer_and_seller_queries_are_scoped_to_the_current_user(self):
		for operation, field in ((orders.get_buyer_orders, "buyer"), (orders.get_seller_orders, "seller")):
			with self.subTest(field=field), patch.object(frappe, "get_all", return_value=[]) as query:
				self.assertEqual(operation(), [])
				self.assertEqual(query.call_args.kwargs["filters"], {field: self.session.user})

	def test_place_order_uses_server_price_and_actor(self):
		product = SimpleNamespace(
			name="PRODUCT-TEST", active=1, stock_qty=10, seller="seller@example.test", selling_price=350
		)
		order = SimpleNamespace(name="ORDER-TEST", order_status="Placed", insert=Mock())
		with patch.object(frappe, "get_doc", side_effect=[product, order]) as get_doc:
			self.assertEqual(
				orders.place_order(product.name, "2"), {"order": "ORDER-TEST", "status": "Placed"}
			)
		payload = get_doc.call_args_list[1].args[0]
		self.assertEqual(payload["buyer"], "buyer@example.test")
		self.assertEqual(payload["seller"], "seller@example.test")
		self.assertEqual(payload["unit_price"], 350)
		self.assertEqual(payload["total_amount"], 700)
		self.assertEqual(payload["payment_status"], "Pending")
		order.insert.assert_called_once_with(ignore_permissions=True)

	def test_invalid_quantity_does_not_create_a_document(self):
		with (
			patch.object(frappe, "get_doc") as get_doc,
			self.assertRaisesRegex(ValueError, "greater than zero"),
		):
			orders.place_order("PRODUCT-TEST", 0)
		get_doc.assert_not_called()

	def test_buyer_cannot_update_seller_order(self):
		order = SimpleNamespace(seller="seller@example.test", order_status="Placed", save=Mock())
		with (
			patch.object(frappe, "get_doc", return_value=order),
			self.assertRaisesRegex(ValueError, "assigned seller"),
		):
			orders.update_order_status("ORDER-TEST", "Packing")
		order.save.assert_not_called()

	def test_closed_order_cannot_be_updated(self):
		self.session.user = "seller@example.test"
		for status in ("Delivered", "Cancelled"):
			order = SimpleNamespace(seller=self.session.user, order_status=status, save=Mock())
			with (
				self.subTest(status=status),
				patch.object(frappe, "get_doc", return_value=order),
				self.assertRaisesRegex(ValueError, "already closed"),
			):
				orders.update_order_status("ORDER-TEST", "Packing")
			order.save.assert_not_called()

	def test_seller_update_saves_then_publishes(self):
		self.session.user = "seller@example.test"
		sequence = []
		order = SimpleNamespace(
			name="ORDER-TEST",
			seller=self.session.user,
			order_status="Placed",
			save=Mock(side_effect=lambda **kwargs: sequence.append("save")),
		)
		with (
			patch.object(frappe, "get_doc", return_value=order),
			patch.object(
				orders, "publish_order_updated", side_effect=lambda value: sequence.append("publish")
			),
		):
			self.assertEqual(
				orders.update_order_status(order.name, "Packing"),
				{"order": "ORDER-TEST", "status": "Packing"},
			)
		self.assertEqual(sequence, ["save", "publish"])
		order.save.assert_called_once_with(ignore_permissions=True)

	def test_event_names_payloads_recipients_and_after_commit_are_preserved(self):
		order = SimpleNamespace(
			name="ORDER-TEST",
			product="PRODUCT-TEST",
			buyer=self.session.user,
			seller="seller@example.test",
			quantity=2,
			total_amount=700,
			order_status="Packing",
		)
		with patch.object(frappe, "publish_realtime") as publish:
			order_events.publish_new_order(order)
			publish.assert_called_once_with(
				"marketplace_new_order",
				{"order": order.name, "product": "Test Product", "quantity": 2, "total_amount": 700},
				user=order.seller,
				after_commit=True,
			)
			publish.reset_mock()
			order_events.publish_order_updated(order)
			publish.assert_called_once_with(
				"marketplace_order_updated",
				{"order": order.name, "status": "Packing", "product": "Test Product"},
				user=order.buyer,
				after_commit=True,
			)

	def test_doctype_after_insert_uses_shared_publisher(self):
		with patch(
			"realtime_marketplace.realtimemarket.doctype.realtime_order.realtime_order.publish_new_order"
		) as publish:
			sentinel = object()
			RealtimeOrder.after_insert(sentinel)
			publish.assert_called_once_with(sentinel)

	def test_mobile_session_shape_is_unchanged(self):
		context = {"user": {"name": self.session.user}, "summary": {"total_orders": 0}}
		with (
			patch.object(sessions, "get_dashboard_context", return_value=context),
			patch.object(sessions, "get_csrf_token", return_value="test-csrf"),
		):
			self.assertEqual(
				sessions.get_mobile_session(), {"sid": "test-session", "csrf_token": "test-csrf", **context}
			)

	def test_existing_and_separated_api_routes_delegate_to_the_same_services(self):
		pairs = [
			(order_api.get_dashboard_context, accounts, "get_dashboard_context"),
			(account_api.get_dashboard_context, accounts, "get_dashboard_context"),
			(order_api.get_active_products, products, "get_active_products"),
			(product_api.get_active_products, products, "get_active_products"),
			(order_api.get_buyer_orders, orders, "get_buyer_orders"),
			(order_api.get_seller_orders, orders, "get_seller_orders"),
			(mobile_api.get_session, sessions, "get_mobile_session"),
		]
		for endpoint, module, name in pairs:
			with (
				self.subTest(endpoint=endpoint.__name__),
				patch.object(module, name, return_value={"ok": True}),
			):
				# mobile imports its service function directly; patch that binding as well.
				if endpoint is mobile_api.get_session:
					with patch.object(mobile_api, "get_mobile_session", return_value={"ok": True}):
						self.assertEqual(endpoint(), {"ok": True})
				else:
					self.assertEqual(endpoint(), {"ok": True})


if __name__ == "__main__":
	unittest.main()
