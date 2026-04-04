from __future__ import annotations

from datetime import date
from enum import Enum

from typing import Any

from pydantic import BaseModel


class SelectionStatus(str, Enum):
    NEEDS_SELECTION = "needs_selection"
    SELECTED = "selected"
    ORDERED = "ordered"
    DELIVERED = "delivered"
    INSTALLED = "installed"
    UNAVAILABLE = "unavailable"
    DISCONTINUED = "discontinued"


class PriceFetchStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    LINK_BROKEN = "link_broken"
    PRODUCT_UNAVAILABLE = "product_unavailable"
    FETCH_ERROR = "fetch_error"


class QuoteStatus(str, Enum):
    NOT_RECEIVED = "not_received"
    RECEIVED = "received"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class DecisionStatus(str, Enum):
    TBD = "tbd"
    RESOLVED = "resolved"


class Project(BaseModel):
    name: str
    status: str
    last_updated: str


class Phase(BaseModel):
    id: str
    name: str
    order: int
    categories: list[str]


class ScopeSection(BaseModel):
    section: str | None = None
    items: list[Any]  # str, list[str], or dict — supports nested bullet points


class Quote(BaseModel):
    status: QuoteStatus = QuoteStatus.NOT_RECEIVED
    amount: float | None = None
    received_date: str | None = None


class MaterialSelection(BaseModel):
    id: str
    item_name: str
    description: str
    status: SelectionStatus = SelectionStatus.NEEDS_SELECTION
    brand: str | None = None
    model: str | None = None
    color: str | None = None
    supplier_name: str | None = None
    product_url: str | None = None
    unit_price: float | None = None
    unit: str = "each"
    quantity: float | None = None
    waste_factor: float = 0.10
    subtotal: float | None = None
    tax_rate: float = 0.06
    tax_amount: float | None = None
    total_with_tax: float | None = None
    price_validated_date: str | None = None
    price_fetch_status: PriceFetchStatus = PriceFetchStatus.PENDING
    notes: str | None = None

    def recalculate(self) -> None:
        if self.unit_price is not None and self.quantity is not None:
            effective_qty = self.quantity * (1 + self.waste_factor)
            self.subtotal = round(self.unit_price * effective_qty, 2)
            self.tax_amount = round(self.subtotal * self.tax_rate, 2)
            self.total_with_tax = round(self.subtotal + self.tax_amount, 2)


class Contractor(BaseModel):
    id: str
    name: str
    phase: str
    related_suppliers: list[str] = []
    warranty: str | None = None
    scope: list[ScopeSection] = []
    quote: Quote = Quote()


class Supplier(BaseModel):
    id: str
    name: str
    related_contractors: list[str] = []
    materials: list[ScopeSection] = []
    selections: list[MaterialSelection] = []


class Decision(BaseModel):
    id: str
    category: str
    description: str
    status: DecisionStatus = DecisionStatus.TBD
    resolved_value: str | None = None
    resolved_date: str | None = None


class ReferenceDoc(BaseModel):
    name: str
    filename: str


class ReferenceDocs(BaseModel):
    house_plans: list[ReferenceDoc] = []
    civil_engineer: list[ReferenceDoc] = []


class MaterialTakeoff(BaseModel):
    briefing: Any = None
    checklist: Any = None


class BalfourProject(BaseModel):
    project: Project
    phases: list[Phase]
    contractors: list[Contractor]
    suppliers: list[Supplier]
    decisions: list[Decision]
    reference_docs: ReferenceDocs
    material_takeoff: MaterialTakeoff | None = None
