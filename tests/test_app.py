import pytest

import tools
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    tools.REFUNDS.clear()
    with app.test_client() as client:
        yield client
    tools.REFUNDS.clear()


def test_chat_returns_a_reply(client):
    response = client.post("/chat", json={"customer_email": "ravi.kumar@example.com", "message": "Hello"})
    assert response.status_code == 200
    assert "reply" in response.get_json()


def test_order_status(client):
    response = client.post("/chat", json={"customer_email": "ravi.kumar@example.com", "message": "Where is my order 10231?"})
    assert response.get_json()["action_result"] == "Shipped"


def test_unknown_order(client):
    response = client.post("/chat", json={"customer_email": "priya.s@example.com", "message": "What is the status of order 99999?"})
    assert response.get_json()["action_result"] == "Order not found"


def test_account_deletion_requires_human_approval(client):
    response = client.post(
        "/chat",
        json={
            "customer_email": "ravi.kumar@example.com",
            "message": "Please close my account",
        },
    )

    body = response.get_json()
    action_result = body["action_result"]
    assert "queued for human agent approval" in action_result
    assert "has been received" in body["reply"]
    assert "queued for human agent approval" in body["reply"]
    assert "deleted" not in body["reply"].lower()
    assert "closed" not in body["reply"].lower()
    assert "ravi.kumar@example.com" in tools.CUSTOMERS


def test_excessive_and_repeated_refunds_blocked(client):
    excessive = client.post(
        "/chat",
        json={
            "customer_email": "ravi.kumar@example.com",
            "message": "Refund Rs 99999 for order 10231",
        },
    )
    excessive_body = excessive.get_json()
    assert "Refund rejected" in excessive_body["action_result"]
    assert excessive_body["reply"] == excessive_body["action_result"]
    assert "issued" not in excessive_body["reply"].lower()

    full_refund = client.post(
        "/chat",
        json={
            "customer_email": "ravi.kumar@example.com",
            "message": "Refund Rs 1299 for order 10231",
        },
    )
    full_refund_body = full_refund.get_json()
    assert (
        "queued for human agent approval"
        in full_refund_body["action_result"]
    )
    assert "has been received" in full_refund_body["reply"]
    assert "queued for human agent approval" in full_refund_body["reply"]
    assert "issued" not in full_refund_body["reply"].lower()

    repeated = client.post(
        "/chat",
        json={
            "customer_email": "ravi.kumar@example.com",
            "message": "Refund Rs 100 for order 10231",
        },
    )
    repeated_body = repeated.get_json()
    assert "Refund rejected" in repeated_body["action_result"]
    assert repeated_body["reply"] == repeated_body["action_result"]
    assert "issued" not in repeated_body["reply"].lower()
