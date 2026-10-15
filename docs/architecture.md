# Custom marketplace architecture

This structure belongs only to the custom `realtime_marketplace` app in
`/home/frappe/realtime-dev/apps/realtime_marketplace`. Frappe core, bench
configuration, site data, and the built-in framework apps are not reorganized.

## Where code belongs

```text
realtime_marketplace/
  api/
    accounts.py                 Profile and dashboard HTTP entry points
    products.py                 Catalog HTTP entry points
    orders.py                   Order HTTP entry points and legacy routes
    mobile.py                   Authenticated mobile session entry point
  services/
    accounts.py                 Current-user identity and account summary queries
    products.py                 Available-product queries
    orders.py                   Actor-scoped order reads, creation, status updates
    sessions.py                 Mobile session and CSRF bootstrap
  permissions.py                Shared authenticated-user guard
  constants.py                  DocType names, statuses, and event names
  serializers/
    orders.py                   Order response fields and product display names
  realtime/
    order_events.py             User-scoped, after-commit event payloads
  realtimemarket/doctype/
    realtime_order/
      realtime_order.json       Existing Frappe schema; required path preserved
      realtime_order.py         Creation validation and after_insert lifecycle
    realtime_product/
      realtime_product.json     Existing Frappe schema; required path preserved
      realtime_product.py       Product DocType controller
  tests/
    test_services.py            Isolated custom service and API regression tests
docs/
  architecture.md               This guide
```

The scaffold packages, `hooks.py`, `modules.txt`, DocType metadata, and generated
DocType client scripts stay in their Frappe-managed locations. Do not rename or
move a DocType directory to match the service layout: Frappe discovers its
controller and schema from that directory.

## Request flow

1. A whitelisted function in `api` receives the request and calls a service.
2. The service verifies the caller, queries Frappe ORM, or applies a command.
3. Order creation uses `Document.insert`, so the DocType validates creation
   invariants and publishes its new-order event from `after_insert`.
4. Order status commands save the document and call the shared status publisher.
5. Publishers use `after_commit=True`, preserving the original transaction timing.
6. Serializers produce the existing mobile/web response fields.

Frappe already supplies the ORM and document lifecycle. An extra generic
repository layer is not needed for these operations.

## Dependency rules

- API wrappers may import services.
- Services may import authentication guards, constants, serializers, and publishers.
- Services must not depend on API wrappers or client UI.
- DocType controllers own document lifecycle validation and call shared publishers.
- Publishers build event payloads and choose recipients; they do not perform
  order commands or commit database transactions.
- Keep new business rules in the owning service or DocType lifecycle. Keep
  formatting of API responses in serializers.
- Keep caller filters alongside queries that use `ignore_permissions=True`.
  These operations intentionally reproduce the original behavior for Website Users.

## Stable HTTP routes

Existing mobile and web clients continue to use all of these methods:

| Method path suffix | Responsibility |
| --- | --- |
| `api.orders.get_dashboard_context` | Legacy account-summary route |
| `api.orders.get_active_products` | Legacy catalog route |
| `api.orders.get_buyer_orders` | Current buyer's purchases |
| `api.orders.get_seller_orders` | Current seller's assigned orders |
| `api.orders.place_order` | Create an order |
| `api.orders.update_order_status` | Assigned seller changes status |
| `api.mobile.get_session` | Current mobile session, CSRF token, identity, summary |

Prefix each suffix with `realtime_marketplace.` when using
`/api/method/<method>`.

For new integrations, separated account/catalog routes are also available as
`realtime_marketplace.api.accounts.get_dashboard_context` and
`realtime_marketplace.api.products.get_active_products`. They call the same
services as the compatibility routes. Existing clients need no changes.

The private `api.orders._require_login` and `_serialize_order` aliases are kept
for compatibility with the earlier mobile bootstrap template. New code should
import their implementations from `permissions` and `serializers.orders`.

## Realtime behavior

- `marketplace_new_order` is delivered to the assigned seller.
- `marketplace_order_updated` is delivered to the buyer.
- Both events publish only after a successful database commit.
- Event names and payload shapes are unchanged.
- As before, status-update notifications are emitted by the order status service;
  editing a field directly in Desk does not call that command automatically.

This is a code organization change. It does not add stock reservation, payments,
status-transition rules, schema changes, fixtures, or new user accounts.

## Adding the next feature

Add a focused `api/<feature>.py` wrapper and `services/<feature>.py` implementation.
Add serializers or realtime helpers only when the feature needs them. Use an
existing DocType's controller for document lifecycle invariants; use Frappe's
normal tooling for new DocTypes and migrations. Add regression coverage for
permissions, response compatibility, and event recipients when those change.

Do not put new business logic in `hooks.py` or expand `api/orders.py` into a
general-purpose module.

## Checks

From the bench directory, these unit tests run without creating or changing
database records:

```bash
cd /home/frappe/realtime-dev
PYTHONPATH=apps/frappe:apps/realtime_marketplace env/bin/python -m unittest realtime_marketplace.tests.test_services -v
```

From the custom app directory, use the Ruff configuration in `pyproject.toml`
to format and lint changed custom Python modules. Full DocType integration tests
can run with Bench on a dedicated test site when lifecycle or schemas change.
