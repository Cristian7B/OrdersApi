"""Basic unit tests for the Pedidos API."""

import pytest
from fastapi.testclient import TestClient

from main import app, orders_db


@pytest.fixture(autouse=True)
def clear_db():
    """Reset in-memory database before every test."""
    orders_db.clear()
    yield
    orders_db.clear()


client = TestClient(app)

VALID_PAYLOAD = {
    "customer_name": "Juan Pérez",
    "products": ["Widget A", "Gadget B"],
    "quantities": [2, 5],
    "shipping_address": "Calle Falsa 123, CDMX",
}


# ---------------------------------------------------------------------------
# POST /orders
# ---------------------------------------------------------------------------
def test_create_order_returns_201():
    response = client.post("/orders", json=VALID_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "Pendiente"
    assert data["customer_name"] == VALID_PAYLOAD["customer_name"]
    assert "id" in data
    assert "created_at" in data


def test_create_order_mismatched_lengths_returns_422():
    payload = {**VALID_PAYLOAD, "quantities": [1]}  # mismatched
    response = client.post("/orders", json=payload)
    assert response.status_code == 422


def test_create_order_missing_field_returns_422():
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "shipping_address"}
    response = client.post("/orders", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /orders
# ---------------------------------------------------------------------------
def test_list_orders_empty():
    response = client.get("/orders")
    assert response.status_code == 200
    assert response.json() == []


def test_list_orders_returns_all():
    client.post("/orders", json=VALID_PAYLOAD)
    client.post("/orders", json={**VALID_PAYLOAD, "customer_name": "Ana García"})
    response = client.get("/orders")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_orders_filter_by_status():
    r1 = client.post("/orders", json=VALID_PAYLOAD).json()
    client.post("/orders", json={**VALID_PAYLOAD, "customer_name": "Ana García"})

    # Promote first order to "Enviado"
    client.put(f"/orders/{r1['id']}/status", json={"status": "Enviado"})

    response = client.get("/orders?status=Enviado")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "Enviado"


def test_list_orders_invalid_status_returns_400():
    response = client.get("/orders?status=Desconocido")
    assert response.status_code == 400


def test_list_orders_invalid_order_param_returns_400():
    response = client.get("/orders?order=random")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# PUT /orders/{id}/status
# ---------------------------------------------------------------------------
def test_update_status_success():
    order_id = client.post("/orders", json=VALID_PAYLOAD).json()["id"]
    response = client.put(f"/orders/{order_id}/status", json={"status": "En Proceso"})
    assert response.status_code == 200
    assert response.json()["status"] == "En Proceso"


def test_update_status_invalid_value_returns_400():
    order_id = client.post("/orders", json=VALID_PAYLOAD).json()["id"]
    response = client.put(f"/orders/{order_id}/status", json={"status": "Invalido"})
    assert response.status_code == 400


def test_update_status_not_found_returns_404():
    response = client.put("/orders/nonexistent-id/status", json={"status": "Enviado"})
    assert response.status_code == 404
