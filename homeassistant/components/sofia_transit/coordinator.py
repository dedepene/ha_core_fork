from __future__ import annotations

import logging
from datetime import timedelta
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
            lines = []
            for bus in raw_data.values():
                details = bus.get("details", [])
                next_bus = details[0].get("t") if details else None
                bus_type = bus.get("type")
                name = bus.get("name")
                match bus_type:
                    case 1:
                        prefix = "A"  # bus
                    case 2:
                        prefix = "TM"  # tram
                    case 3:
                        prefix = "M"  # metro
                    case 4:
                        prefix = "TB"  # trolley
                    case 5:
                        prefix = "N"  # night line
                    case _:
                        prefix = ""
                full_line = f"{prefix}{name}" if prefix else name
                lines.append({"line": full_line, "next_bus": next_bus})
            _LOGGER.debug("Lines received: %s", lines)
            return {"lines": lines}
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
