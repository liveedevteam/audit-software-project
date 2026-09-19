# Flow validation (fictional sample)

## Checkout
Customer pays; an order, a payment record and a stock update are written.

| Step / handler | Caller | Checked | Atomic | On failure | Location |
|---|---|---|---|---|---|
| POST /checkout | any signed-in customer | authentication only, no tenant check on the cart | no: three independent writes | order can exist without a payment record | src/checkout/checkout.service.ts:120-168 |

Findings: DB-001 (writes not in one transaction), TEN-001 (records reachable across tenants by id).
Correctly protected: payment provider webhook verifies its signature before touching the payload.
Not traced: refund flow.
