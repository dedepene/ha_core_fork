from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_URL, UPDATE_INTERVAL
from .helpers import async_fetch_data_from_sofiatraffic

_LOGGER = logging.getLogger(__name__)


class SofiaTransitUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Sofia Transit data."""

    def __init__(self, hass: HomeAssistant, session) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="SofiaTransit Update Coordinator",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.session = session

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and transform data from Sofia Transit API."""
        try:
            raw_data = await async_fetch_data_from_sofiatraffic(
                API_URL, self.session, {"stop": "1287"}
            )
            # Transform raw API response into a dict with a "lines" list:
            lines = []
            for bus in raw_data.values():
                details = bus.get("details", [])
                next_bus = details[0].get("t") if details else None
                lines.append({"line": bus.get("name"), "next_bus": next_bus})
            print(f"lines: {lines}")
            return {"lines": lines}
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
