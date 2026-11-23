ORDERS = {
    "10231": {"status": "Shipped", "amount": 1299},
    "10232": {"status": "Delivered", "amount": 499},
    "10233": {"status": "Processing", "amount": 2499},
}

CUSTOMERS = {
    "ravi.kumar@example.com": {
        "name": "Ravi Kumar",
        "phone": "+91 98480 12345",
        "active": True,
    },
    "priya.s@example.com": {
        "name": "Priya Sharma",
        "phone": "+91 99890 67890",
        "active": True,
    },
}

REFUNDS = []


def get_order_status(order_id: str):
    order = ORDERS.get(order_id)
    return order["status"] if order else "Order not found"


def issue_refund(order_id: str, amount: int):
    order = ORDERS.get(str(order_id))
    if order is None:
        return "Refund rejected: order not found"

    already_refunded = sum(
        refund["amount"]
        for refund in REFUNDS
        if refund["order_id"] == str(order_id)
    )
    remaining = order["amount"] - already_refunded

    if type(amount) is not int or amount <= 0:
        return "Refund rejected: amount must be a positive whole number"
    if amount > remaining:
        return "Refund rejected: amount exceeds the remaining refundable amount"

    REFUNDS.append(
        {
            "order_id": str(order_id),
            "amount": amount,
            "status": "pending_approval",
        }
    )
    return (
        f"Refund of Rs {amount} for order {order_id} "
        "queued for human agent approval"
    )


def delete_customer_account(customer_email: str):
    return (
        f"Account closure for {customer_email} "
        "queued for human agent approval"
    )


ALLOWED_TOOLS = {
    "get_order_status": get_order_status,
    "issue_refund": issue_refund,
    "delete_customer_account": delete_customer_account,
}
