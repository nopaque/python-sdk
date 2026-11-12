"""Numbers resource - /numbers.

The phone numbers a workspace rents: caller IDs for its tests and the numbers
its systems dial back. Ordering one spends money; see :meth:`NumbersResource.order`.
"""
from __future__ import annotations

from typing import List, Optional

from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.numbers import (
    AvailableNumbers,
    NumberList,
    NumberOrder,
    NumberOrderStatus,
    NumberRelease,
    NumberRequirements,
    NumberType,
    NumberUse,
    OrderablePhoneNumberType,
    PhoneNumber,
)

__all__ = ["AsyncNumbersResource", "NumbersResource"]


def _available_params(
    *,
    country: str,
    phone_number_type: Optional[str],
    number_type: Optional[str],
    limit: Optional[int],
) -> dict:
    params: dict = {"country": country}
    if phone_number_type is not None:
        params["phoneNumberType"] = phone_number_type
    if number_type is not None:
        params["numberType"] = number_type
    if limit is not None:
        params["limit"] = limit
    return params


def _requirements_params(*, country: str, phone_number_type: Optional[str]) -> dict:
    params: dict = {"country": country}
    if phone_number_type is not None:
        params["phoneNumberType"] = phone_number_type
    return params


def _order_body(
    *,
    e164: str,
    number_type: str,
    country: str,
    phone_number_type: Optional[str],
) -> dict:
    body: dict = {"e164": e164, "numberType": number_type, "country": country}
    if phone_number_type is not None:
        body["phoneNumberType"] = phone_number_type
    return body


def _update_body(*, uses: Optional[List[NumberUse]], is_default: Optional[bool]) -> dict:
    if uses is None and is_default is None:
        raise ValueError("numbers.update() needs at least one of uses or is_default")
    body: dict = {}
    if uses is not None:
        body["uses"] = list(uses)
    if is_default is not None:
        body["isDefault"] = is_default
    return body


class NumbersResource(SyncResource):
    """Synchronous /numbers endpoints."""

    def list(self, *, request_options: RequestOptions | None = None) -> NumberList:
        """Every number the workspace holds, newest first, with its allowance.

        Not paginated. A workspace renting no numbers gets an empty list.
        """
        raw = self._transport.request("GET", "/numbers", request_options=request_options)
        return NumberList.model_validate(raw)

    def list_available(
        self,
        *,
        country: str,
        phone_number_type: str | None = None,
        number_type: NumberType | None = None,
        limit: int | None = None,
        request_options: RequestOptions | None = None,
    ) -> AvailableNumbers:
        """Search for numbers that can be ordered. Nothing is bought.

        ``number_type`` (server default ``survey``) decides the capability
        filter. Omit ``phone_number_type`` to search every type that can do
        the job, cheapest first. ``limit`` is clamped to 1-50 (default 10).
        """
        raw = self._transport.request(
            "GET",
            "/numbers/available",
            params=_available_params(
                country=country,
                phone_number_type=phone_number_type,
                number_type=number_type,
                limit=limit,
            ),
            request_options=request_options,
        )
        return AvailableNumbers.model_validate(raw)

    def get_requirements(
        self,
        *,
        country: str,
        phone_number_type: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> NumberRequirements:
        """The regulatory items a country asks for before it activates a number.

        Information, not a form: nopaque satisfies every item on the
        customer's behalf.
        """
        raw = self._transport.request(
            "GET",
            "/numbers/requirements",
            params=_requirements_params(country=country, phone_number_type=phone_number_type),
            request_options=request_options,
        )
        return NumberRequirements.model_validate(raw)

    def order(
        self,
        *,
        e164: str,
        number_type: NumberType,
        country: str,
        phone_number_type: OrderablePhoneNumberType | None = None,
        request_options: RequestOptions | None = None,
    ) -> NumberOrder:
        """Order a number. **This spends money.**

        A number carries a recurring monthly charge, and an order cannot be
        undone by retrying: a repeat request is a second number and a second
        charge. The SDK retries a POST only when the request never reached
        the API (a 429, or a connection failure before sending); do not wrap
        this in a retry loop of your own.

        ``e164`` is a number exactly as :meth:`list_available` returned it.
        ``number_type`` is what the number is for, and decides the capabilities
        it must have (a ``survey`` number must carry SMS). ``country`` is ISO
        3166-1 alpha-2; only ``GB`` is sold today. ``phone_number_type``
        defaults to the cheapest type that can do the job.

        A number that activates at once comes back ``live``. Otherwise it is
        ``ordering`` and ``order_id`` is set; follow it with :meth:`get_order`.
        Release a number you no longer need with :meth:`release`.
        """
        raw = self._transport.request(
            "POST",
            "/numbers/orders",
            json=_order_body(
                e164=e164,
                number_type=number_type,
                country=country,
                phone_number_type=phone_number_type,
            ),
            request_options=request_options,
        )
        return NumberOrder.model_validate(raw)

    def get_order(
        self, order_id: str, *, request_options: RequestOptions | None = None
    ) -> NumberOrderStatus:
        """Progress on an order, per regulatory requirement.

        Read this rather than the number's state: it names what is still
        outstanding and who the order is waiting on.
        """
        raw = self._transport.request(
            "GET", f"/numbers/orders/{order_id}", request_options=request_options
        )
        return NumberOrderStatus.model_validate(raw)

    def update(
        self,
        number_id: str,
        *,
        uses: List[NumberUse] | None = None,
        is_default: bool | None = None,
        request_options: RequestOptions | None = None,
    ) -> PhoneNumber:
        """Set a number's use, its default flag, or both. Send at least one.

        ``uses`` is a one-element list: a number has one use. ``is_default=True``
        makes it the workspace's fallback caller ID and clears the flag from
        any other number.
        """
        raw = self._transport.request(
            "PATCH",
            f"/numbers/{number_id}",
            json=_update_body(uses=uses, is_default=is_default),
            request_options=request_options,
        )
        return PhoneNumber.model_validate(raw.get("number", raw))

    def release(
        self, number_id: str, *, request_options: RequestOptions | None = None
    ) -> NumberRelease:
        """Release a number the workspace rents. Billing for it stops.

        The number goes back to nopaque's pool and is not reserved for you.
        Only a ``live`` number can be released.
        """
        raw = self._transport.request(
            "POST", f"/numbers/{number_id}/release", request_options=request_options
        )
        return NumberRelease.model_validate(raw or {})


class AsyncNumbersResource(AsyncResource):
    """Asynchronous /numbers endpoints."""

    async def list(self, *, request_options: RequestOptions | None = None) -> NumberList:
        """Every number the workspace holds, newest first, with its allowance."""
        raw = await self._transport.request(
            "GET", "/numbers", request_options=request_options
        )
        return NumberList.model_validate(raw)

    async def list_available(
        self,
        *,
        country: str,
        phone_number_type: str | None = None,
        number_type: NumberType | None = None,
        limit: int | None = None,
        request_options: RequestOptions | None = None,
    ) -> AvailableNumbers:
        """Search for numbers that can be ordered. Nothing is bought."""
        raw = await self._transport.request(
            "GET",
            "/numbers/available",
            params=_available_params(
                country=country,
                phone_number_type=phone_number_type,
                number_type=number_type,
                limit=limit,
            ),
            request_options=request_options,
        )
        return AvailableNumbers.model_validate(raw)

    async def get_requirements(
        self,
        *,
        country: str,
        phone_number_type: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> NumberRequirements:
        """The regulatory items a country asks for before it activates a number."""
        raw = await self._transport.request(
            "GET",
            "/numbers/requirements",
            params=_requirements_params(country=country, phone_number_type=phone_number_type),
            request_options=request_options,
        )
        return NumberRequirements.model_validate(raw)

    async def order(
        self,
        *,
        e164: str,
        number_type: NumberType,
        country: str,
        phone_number_type: OrderablePhoneNumberType | None = None,
        request_options: RequestOptions | None = None,
    ) -> NumberOrder:
        """Order a number. **This spends money.**

        A number carries a recurring monthly charge, and an order cannot be
        undone by retrying: a repeat request is a second number and a second
        charge. The SDK retries a POST only when the request never reached
        the API (a 429, or a connection failure before sending); do not wrap
        this in a retry loop of your own.

        ``e164`` is a number exactly as :meth:`list_available` returned it.
        ``number_type`` is what the number is for, and decides the capabilities
        it must have (a ``survey`` number must carry SMS). ``country`` is ISO
        3166-1 alpha-2; only ``GB`` is sold today. ``phone_number_type``
        defaults to the cheapest type that can do the job.

        A number that activates at once comes back ``live``. Otherwise it is
        ``ordering`` and ``order_id`` is set; follow it with :meth:`get_order`.
        Release a number you no longer need with :meth:`release`.
        """
        raw = await self._transport.request(
            "POST",
            "/numbers/orders",
            json=_order_body(
                e164=e164,
                number_type=number_type,
                country=country,
                phone_number_type=phone_number_type,
            ),
            request_options=request_options,
        )
        return NumberOrder.model_validate(raw)

    async def get_order(
        self, order_id: str, *, request_options: RequestOptions | None = None
    ) -> NumberOrderStatus:
        """Progress on an order, per regulatory requirement."""
        raw = await self._transport.request(
            "GET", f"/numbers/orders/{order_id}", request_options=request_options
        )
        return NumberOrderStatus.model_validate(raw)

    async def update(
        self,
        number_id: str,
        *,
        uses: List[NumberUse] | None = None,
        is_default: bool | None = None,
        request_options: RequestOptions | None = None,
    ) -> PhoneNumber:
        """Set a number's use, its default flag, or both. Send at least one."""
        raw = await self._transport.request(
            "PATCH",
            f"/numbers/{number_id}",
            json=_update_body(uses=uses, is_default=is_default),
            request_options=request_options,
        )
        return PhoneNumber.model_validate(raw.get("number", raw))

    async def release(
        self, number_id: str, *, request_options: RequestOptions | None = None
    ) -> NumberRelease:
        """Release a number the workspace rents. Billing for it stops."""
        raw = await self._transport.request(
            "POST", f"/numbers/{number_id}/release", request_options=request_options
        )
        return NumberRelease.model_validate(raw or {})
