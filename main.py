from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title="Pedidos API", version="1.0.0")

# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------
orders_db: list[dict] = []

VALID_STATUSES = {"Pendiente", "En Proceso", "Enviado", "Entregado"}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=1)
    products: list[str] = Field(..., min_items=1)
    quantities: list[int] = Field(..., min_items=1)
    shipping_address: str = Field(..., min_length=1)


class StatusUpdate(BaseModel):
    status: str


class OrderResponse(BaseModel):
    id: str
    customer_name: str
    products: list[str]
    quantities: list[int]
    shipping_address: str
    status: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.post("/orders", response_model=OrderResponse, status_code=201)
def create_order(order: OrderCreate):
    """Create a new order with status 'Pendiente'."""
    if len(order.products) != len(order.quantities):
        raise HTTPException(
            status_code=422,
            detail="'products' and 'quantities' must have the same length.",
        )

    new_order = {
        "id": str(uuid4()),
        "customer_name": order.customer_name,
        "products": order.products,
        "quantities": order.quantities,
        "shipping_address": order.shipping_address,
        "status": "Pendiente",
        "created_at": datetime.now(timezone.utc),
    }
    orders_db.append(new_order)
    return new_order


@app.get("/orders", response_model=list[OrderResponse])
def list_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    order: str = Query("asc", description="Sort by date: 'asc' or 'desc'"),
):
    """List all orders, optionally filtered by status and sorted by creation date."""
    if status and status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Valid values: {sorted(VALID_STATUSES)}",
        )
    if order not in ("asc", "desc"):
        raise HTTPException(status_code=400, detail="'order' must be 'asc' or 'desc'.")

    result = [o for o in orders_db if o["status"] == status] if status else list(orders_db)
    result.sort(key=lambda o: o["created_at"], reverse=(order == "desc"))
    return result


@app.put("/orders/{order_id}/status", response_model=OrderResponse)
def update_status(order_id: str, body: StatusUpdate):
    """Update the status of an existing order."""
    if body.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Valid values: {sorted(VALID_STATUSES)}",
        )

    for order in orders_db:
        if order["id"] == order_id:
            order["status"] = body.status
            return order

    raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")

