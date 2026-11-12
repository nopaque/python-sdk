"""Models for /numbers endpoints."""
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict


def _alias(name: str) -> str:
    """snake_case field name -> camelCase wire name."""
    head, *rest = name.split("_")
    return head + "".join(word.capitalize() for word in rest)


#: What a number is used for. Determines the carrier capabilities it needs:
#: a ``survey`` number must carry SMS.
NumberType = Literal["outbound", "inbound", "callback", "survey"]
#: A number's single current use, set with ``numbers.update(uses=[...])``.
#: ``outbound`` and ``load`` are caller IDs; the rest are destinations.
NumberUse = Literal["outbound", "load", "callback", "survey", "inbound"]
#: The carrier's classification of a number that can be ordered.
OrderablePhoneNumberType = Literal["national", "local", "mobile"]


class _NumbersBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


class PhoneNumber(_NumbersBase):
    """A number the workspace holds, as ``GET /numbers`` reports it.

    ``state`` is ``ordering`` (not usable yet, see ``requirements_status``),
    ``live``, ``releasing``, ``pooled``, ``platform``, ``deleted`` or
    ``failed``. Enum-like fields are typed ``str`` so a new server value never
    makes a read raise.
    """

    number_id: str
    order_id: Optional[str] = None
    e164: str
    country_iso2: Optional[str] = None
    phone_number_type: Optional[str] = None
    capabilities: List[str] = []
    type: Optional[str] = None
    uses: List[str] = []
    is_default: Optional[bool] = None
    state: Optional[str] = None
    requirements_status: Optional[str] = None
    monthly_rate_usd: Optional[float] = None
    acquired_at: Optional[str] = None
    failed_at: Optional[str] = None
    created_at: Optional[str] = None


class NumberAllowance(_NumbersBase):
    """How many numbers the workspace may hold. ``max`` and ``remaining`` are
    None when ``unlimited``."""

    used: int
    max: Optional[int] = None
    remaining: Optional[int] = None
    unlimited: bool
    source: Optional[str] = None
    tier: Optional[str] = None
    included_in_deal: Optional[bool] = None
    deal_ref: Optional[str] = None


class NumberList(_NumbersBase):
    """Response for ``GET /numbers``: every number held, newest first."""

    numbers: List[PhoneNumber] = []
    allowance: Optional[NumberAllowance] = None


class AvailableNumber(_NumbersBase):
    """A number that can be ordered.

    ``from_pool`` numbers are already held by nopaque: no setup fee, and they
    work immediately. ``self_serve=False`` numbers are sold through sales only.
    """

    e164: str
    from_pool: Optional[bool] = None
    phone_number_type: Optional[str] = None
    capabilities: List[str] = []
    monthly_rate_usd: Optional[float] = None
    upfront_rate_usd: Optional[float] = None
    self_serve: Optional[bool] = None
    currency: Optional[str] = None
    immediate_activation: Optional[bool] = None


class AvailableNumbers(_NumbersBase):
    """Response for ``GET /numbers/available``."""

    country: str
    phone_number_type: Optional[str] = None
    #: Every type actually searched.
    phone_number_types: List[str] = []
    number_type: Optional[str] = None
    numbers: List[AvailableNumber] = []


class NumberRequirement(_NumbersBase):
    """One regulatory item a country asks for. Always ``satisfied_by="nopaque"``:
    the customer supplies nothing."""

    id: str
    name: str
    field_type: Optional[str] = None
    description: Optional[str] = None
    acceptance_criteria: Optional[Dict[str, Any]] = None
    satisfied_by: Optional[str] = None


class NumberRequirements(_NumbersBase):
    """Response for ``GET /numbers/requirements``. Information, not a form."""

    country: str
    phone_number_type: Optional[str] = None
    requirements: List[NumberRequirement] = []


class NumberActivation(_NumbersBase):
    immediate: Optional[bool] = None
    message: Optional[str] = None


class NumberOrder(_NumbersBase):
    """Response for ``POST /numbers/orders``.

    A number that activates immediately comes back ``live`` with no
    ``order_id``. Otherwise it is ``ordering`` and ``order_id`` is set: follow
    it with ``numbers.get_order(order_id)``.
    """

    number: PhoneNumber
    order_id: Optional[str] = None
    from_pool: Optional[bool] = None
    activation: Optional[NumberActivation] = None
    requirements_submitted: Optional[bool] = None
    premium_charged_usd: Optional[float] = None
    upfront_charged_usd: Optional[float] = None
    monthly_rate_usd: Optional[float] = None


class NumberOrderOutstandingItem(_NumbersBase):
    requirement_id: Optional[str] = None
    name: Optional[str] = None
    field_type: Optional[str] = None
    status: Optional[str] = None


class NumberOrderProgress(_NumbersBase):
    """Per-requirement progress on an order.

    ``waiting_on`` is ``telnyx`` (the carrier is reviewing), ``nopaque`` or
    ``nobody``. ``complete`` is the carrier's own verdict.
    """

    total: int
    approved: int
    awaiting_on: int
    outstanding: List[NumberOrderOutstandingItem] = []
    waiting_on: str
    complete: bool
    requirements_status: Optional[str] = None
    customer_must_act: Optional[bool] = None
    deadline: Optional[str] = None


class NumberOrderStatus(_NumbersBase):
    """Response for ``GET /numbers/orders/{orderId}``."""

    order_id: str
    number: PhoneNumber
    progress: NumberOrderProgress


class NumberRelease(_NumbersBase):
    """Response for ``POST /numbers/{numberId}/release``."""

    released: Optional[bool] = None
    message: Optional[str] = None
