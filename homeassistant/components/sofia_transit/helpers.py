import time
from typing import Any
from urllib.parse import unquote

import aiohttp

TOKEN_LIFESPAN: int = 7200  # tokens lifespan in seconds (2 hours)
sofiatraffic_session_cookie: str | None = None
sofiatraffic_xsrf_token: str | None = None
tokens_last_refreshed: float | None = None


async def async_fetch_tokens(session: aiohttp.ClientSession) -> None:
    """Asynchronously fetch and update tokens from SofiaTraffic."""
    global sofiatraffic_session_cookie, sofiatraffic_xsrf_token, tokens_last_refreshed
    # Perform an asynchronous HEAD request
    async with session.head(
        "https://sofiatraffic.bg/bg/public-transport", allow_redirects=False
    ) as response:
        # aiohttp stores headers in a case-insensitive multidict
        cookies = response.headers.getall("Set-Cookie", [])
    for cookie in cookies:
        if cookie.startswith("XSRF-TOKEN="):
            sofiatraffic_xsrf_token = unquote(cookie.split(";", 1)[0].split("=", 1)[1])
        elif cookie.startswith("sofia_traffic_session="):
            sofiatraffic_session_cookie = unquote(
                cookie.split(";", 1)[0].split("=", 1)[1]
            )
    tokens_last_refreshed = time.time()
    print(
        f"xsrf-token: {sofiatraffic_xsrf_token}  session cookie: {sofiatraffic_session_cookie}"
    )


async def async_fetch_data_from_sofiatraffic(
    url: str, session: aiohttp.ClientSession, body: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Asynchronously fetch data from SofiaTraffic."""
    if body is None:
        body = {"stop": "1287"}
    # Refresh tokens if missing or expired
    if (
        sofiatraffic_session_cookie is None
        or sofiatraffic_xsrf_token is None
        or tokens_last_refreshed is None
        or (time.time() - tokens_last_refreshed > TOKEN_LIFESPAN)
    ):
        await async_fetch_tokens(session)
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/134.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-GB,en;q=0.5",
        # Remove brotli and zstd encodings so the server responds with gzip/deflate only.
        "Accept-Encoding": "gzip, deflate",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/json",
        "X-XSRF-TOKEN": sofiatraffic_xsrf_token,
        "Cookie": f"XSRF-TOKEN={sofiatraffic_xsrf_token}; sofia_traffic_session={sofiatraffic_session_cookie}",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "Referer": "https://www.sofiatraffic.bg/bg/public-transport",
        "TE": "trailers",
    }
    async with session.post(url, headers=headers, json=body) as response:
        if "application/json" not in response.content_type:
            text = await response.text()
            raise Exception(
                f"Unexpected content type: {response.content_type}. Response: {text}"
            )
        return await response.json()
