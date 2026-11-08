from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Path, Query, Request
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.adapters.api.limits import IdentityRateLimit
from app.adapters.api.security import ApiSecurity
from app.adapters.storage.operations import OperationsStore
from app.application.custody import CustodyOperations
from app.application.custody_tariffs import Money, PositiveHours, SizeCategory


Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
Contact = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=254)]
PaymentReference = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Version = Annotated[int, Field(strict=True, ge=1)]
Key = Annotated[str, Header(alias="Idempotency-Key", min_length=16, max_length=120)]


class CustodyBody(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CustodyCreate(CustodyBody):
    recipient_contact: Contact
    point_id: UUID
    description: Text
    size_category: SizeCategory


class VersionReason(CustodyBody):
    expected_version: Version
    reason: Text


class Payment(CustodyBody):
    expected_version: Version
    accepted_amount: Money
    payment_method: Literal["EFECTIVO", "REFERENCIA_MANUAL"]
    payment_reference: PaymentReference | None = None


class Receive(Payment):
    location_id: UUID
    duration_hours: PositiveHours
    tariff_id: UUID
    external_condition: Text


class Extension(Payment):
    additional_hours: PositiveHours


def custody_router(store: OperationsStore, security: ApiSecurity) -> APIRouter:
    router = APIRouter(tags=["Custodia"])
    csrf = [Depends(security.csrf)]
    operations = CustodyOperations(store, request_key=security.request_key)
    rates = IdentityRateLimit()

    @router.get("/points")
    def points():
        return operations.points_list()

    @router.get("/points/{point_id}/quote")
    def quote(
        request: Request, point_id: UUID, size_category: SizeCategory,
        duration_hours: Annotated[int, Query(ge=1)], custody_id: UUID | None = None,
    ):
        if custody_id is not None:
            return operations.historical_quote(security.actor(request), point_id, custody_id, size_category, duration_hours)
        return operations.quote(point_id, size_category, duration_hours)

    @router.post("/custodies", status_code=201, dependencies=csrf)
    def register(request: Request, body: CustodyCreate, key: Key):
        actor = security.actor(request)
        rates.check("register_custody", str(actor["id"]), 30)
        return operations.create(actor, key, body.model_dump(), request.state.correlation_id)

    @router.get("/custodies")
    def list_custodies(
        request: Request, point_id: UUID | None = None,
        tracking_number: Annotated[str | None, Query(min_length=1, max_length=32)] = None,
    ):
        return operations.list_custodies(security.actor(request), point_id, tracking_number)

    @router.get("/custodies/{custody_id}")
    def detail(request: Request, custody_id: UUID):
        return operations.detail(security.actor(request), custody_id)

    @router.post("/custodies/{custody_id}/public-reference", dependencies=csrf)
    def rotate(request: Request, custody_id: UUID):
        return operations.rotate_reference(security.actor(request), custody_id, request.state.correlation_id)

    @router.get("/public-tracking/{reference}")
    def tracking(request: Request, reference: Annotated[str, Path(min_length=1, max_length=128)]):
        rates.check("public_tracking", request.client.host if request.client else "unknown", 60)
        return operations.tracking(reference)

    @router.post("/custodies/{custody_id}/cancel", dependencies=csrf)
    def cancel(request: Request, custody_id: UUID, body: VersionReason, key: Key):
        return operations.cancel(security.actor(request), custody_id, key, body.model_dump(), request.state.correlation_id)

    @router.post("/custodies/{custody_id}/receive", dependencies=csrf)
    def receive(request: Request, custody_id: UUID, body: Receive, key: Key):
        return operations.receive(security.actor(request), custody_id, key, body.model_dump(), request.state.correlation_id)

    @router.post("/custodies/{custody_id}/extend", dependencies=csrf)
    def extend(request: Request, custody_id: UUID, body: Extension, key: Key):
        return operations.extend(security.actor(request), custody_id, key, body.model_dump(), request.state.correlation_id)

    @router.get("/inventory")
    def inventory(request: Request, point_id: UUID):
        return operations.inventory(security.actor(request), point_id)

    return router
