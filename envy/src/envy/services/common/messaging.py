from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional

import requests
from requests import Response

from .config import EnvyConfig
from .logging import get_logger


DEFAULT_TIMEOUT = 15
RETRYABLE_STATUS = {502, 503, 504}


class ServiceClient:
    """Simple HTTP client with shared-secret auth for internal service calls."""

    def __init__(
        self,
        base_url: str,
        config: EnvyConfig,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        backoff: float = 0.5,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"x-envy-secret": config.get("messaging.shared_secret", "change-me-envy")}
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff = backoff
        self.logger = get_logger(self.__class__.__name__, config=config)

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_payload: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        last_exc: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.request(
                    method=method.upper(),
                    url=url,
                    headers=self.headers,
                    json=json_payload,
                    data=data,
                    params=params,
                    timeout=self.timeout,
                )
                if response.status_code in RETRYABLE_STATUS:
                    raise requests.HTTPError(f"Retryable status {response.status_code}", response=response)
                return response
            except (requests.RequestException, requests.Timeout) as exc:
                last_exc = exc
                self.logger.warning(
                    f"Request {method} {url} failed (attempt {attempt}/{self.max_retries}): {exc}"
                )
                time.sleep(self.backoff * attempt)
        raise RuntimeError(f"Failed request after {self.max_retries} attempts: {method} {url}") from last_exc

    def post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self._request("POST", path, json_payload=payload)
        return _parse_json(response)

    def get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response = self._request("GET", path, params=params)
        return _parse_json(response)

    def healthcheck(self) -> bool:
        try:
            response = self._request("GET", "/health")
            return response.ok
        except Exception as exc:  # noqa: BLE001
            self.logger.debug("Healthcheck failed: %s", exc)
            return False


def _parse_json(response: Response) -> Dict[str, Any]:
    try:
        response.raise_for_status()
        if not response.content:
            return {}
        return response.json()
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON response from {response.url}") from exc


__all__ = ["ServiceClient"]
