"""Shared names and statuses for the custom marketplace app."""

PRODUCT_DOCTYPE = "Realtime Product"
ORDER_DOCTYPE = "Realtime Order"

INITIAL_ORDER_STATUS = "Placed"
INITIAL_PAYMENT_STATUS = "Pending"
PENDING_ORDER_STATUSES = ("Placed", "Confirmed", "Packing")
UPDATABLE_ORDER_STATUSES = frozenset(
	{"Confirmed", "Packing", "Ready for Pickup", "Out for Delivery", "Delivered", "Cancelled"}
)
CLOSED_ORDER_STATUSES = frozenset({"Delivered", "Cancelled"})

NEW_ORDER_EVENT = "marketplace_new_order"
ORDER_UPDATED_EVENT = "marketplace_order_updated"
