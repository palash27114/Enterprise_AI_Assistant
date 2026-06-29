"""Customer account data from PostgreSQL."""

from datetime import date
from typing import Any

from sqlalchemy import or_, select

from app.db.models import Customer
from app.db.session import get_session


def _customer_to_dict(customer: Customer) -> dict[str, Any]:
    since = customer.since
    return {
        "customer_id": customer.customer_id,
        "name": customer.name,
        "segment": customer.segment,
        "account_manager": customer.account_manager or "",
        "region": customer.region or "",
        "mrr_usd": customer.mrr_usd,
        "status": customer.status,
        "since": since.isoformat() if isinstance(since, date) else str(since or ""),
    }


def list_customers(search: str | None = None) -> list[dict[str, Any]]:
    """Return all customer accounts, optionally filtered by search."""
    with get_session() as session:
        query = select(Customer).order_by(Customer.name)
        if search:
            lowered = f"%{search.lower()}%"
            query = query.where(
                or_(
                    Customer.name.ilike(lowered),
                    Customer.customer_id.ilike(lowered),
                )
            )
        customers = session.scalars(query).all()
        return [_customer_to_dict(customer) for customer in customers]


def get_customer_record(customer_id: str) -> dict[str, Any] | None:
    """Fetch one customer by ID."""
    with get_session() as session:
        customer = session.get(Customer, customer_id.upper())
        if not customer:
            return None
        return _customer_to_dict(customer)
