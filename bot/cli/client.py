"""Thin REST client for Alpaca Trading and Market Data APIs."""

from __future__ import annotations

from typing import Optional, Dict, Any, Iterator
from enum import Enum

import httpx
from loguru import logger


class ApiBase(Enum):
    """Base URL selection."""
    TRADING = "trading"
    DATA = "data"


class AlpacaError(Exception):
    """Raised on non-2xx Alpaca API responses."""

    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(f"[{status_code}] {code}: {message}")


class AlpacaClient:
    """Handles auth, base URLs, HTTP methods, error handling, and pagination.

    Usage:
        client = AlpacaClient()
        account = client.get("/v2/account")
        bars = client.get("/v2/stocks/AAPL/bars", base=ApiBase.DATA,
                          params={"timeframe": "1Day", "limit": 100})
    """

    TRADING_BASE_URLS = {
        "paper": "https://paper-api.alpaca.markets",
        "live": "https://api.alpaca.markets",
    }
    DATA_BASE_URL = "https://data.alpaca.markets"

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        paper: Optional[bool] = None,
    ):
        from bot.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_PAPER_TRADE

        self.api_key = api_key or ALPACA_API_KEY
        self.secret_key = secret_key or ALPACA_SECRET_KEY
        self.paper = paper if paper is not None else ALPACA_PAPER_TRADE

        if not self.api_key or not self.secret_key:
            raise AlpacaError(0, "auth", "ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in .env")

        self._trading_base = (
            self.TRADING_BASE_URLS["paper"] if self.paper
            else self.TRADING_BASE_URLS["live"]
        )
        self._data_base = self.DATA_BASE_URL

        self._http = httpx.Client(
            headers={
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key,
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    def _base_url(self, base: ApiBase) -> str:
        if base == ApiBase.DATA:
            return self._data_base
        return self._trading_base

    def _request(
        self,
        method: str,
        path: str,
        base: ApiBase = ApiBase.TRADING,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Execute HTTP request, handle errors, return parsed JSON."""
        url = self._base_url(base) + path

        # Filter out None params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        response = self._http.request(method, url, params=params, json=json)

        if response.status_code == 204:
            return None

        if response.status_code >= 400:
            try:
                body = response.json()
                raise AlpacaError(
                    response.status_code,
                    body.get("code", str(response.status_code)),
                    body.get("message", response.text),
                )
            except (ValueError, KeyError):
                raise AlpacaError(response.status_code, "unknown", response.text)

        if not response.text:
            return None

        return response.json()

    def get(self, path: str, **kwargs: Any) -> Any:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Any:
        return self._request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> Any:
        return self._request("PATCH", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> Any:
        return self._request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Any:
        return self._request("DELETE", path, **kwargs)

    def paginate(
        self,
        path: str,
        base: ApiBase = ApiBase.TRADING,
        params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        page_token_key: str = "page_token",
        items_key: Optional[str] = None,
    ) -> Iterator[Any]:
        """Auto-paginating iterator for list endpoints.

        Args:
            path: API endpoint path
            base: TRADING or DATA
            params: Query parameters
            limit: Max total items to yield (None = all)
            page_token_key: Query param name for page token
            items_key: If set, extract items from response[items_key]

        Yields:
            Individual items from each page.
        """
        params = dict(params or {})
        count = 0

        while True:
            data = self.get(path, base=base, params=params)

            if items_key and isinstance(data, dict):
                items = data.get(items_key, [])
                next_token = data.get("next_page_token")
            elif isinstance(data, list):
                items = data
                next_token = None
            else:
                items = [data] if data else []
                next_token = None

            for item in items:
                yield item
                count += 1
                if limit and count >= limit:
                    return

            if not next_token:
                break
            params[page_token_key] = next_token

    def close(self) -> None:
        self._http.close()
