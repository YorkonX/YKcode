import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx


class OkxClient:
    def __init__(self, *, api_key: str, secret_key: str, passphrase: str, base_url: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10)

    async def close(self) -> None:
        await self._client.aclose()

    async def fetch_positions(self, inst_type: str | None = None) -> List[Dict[str, Any]]:
        params = {"instType": inst_type} if inst_type else {}
        path = "/api/v5/account/positions"
        headers = self._signed_headers("GET", path, params)
        response = await self._client.get(path, params=params, headers=headers)
        response.raise_for_status()
        payload = response.json()
        return payload.get("data", [])

    def _signed_headers(self, method: str, path: str, params: Dict[str, Any] | None = None, body: Dict[str, Any] | None = None) -> Dict[str, str]:
        timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        query = ""
        if params:
            query = httpx.QueryParams(params).render()
            path = f"{path}?{query}"

        body_str = json.dumps(body) if body else ""
        prehash = f"{timestamp}{method.upper()}{path}{body_str}"
        signature = hmac.new(
            self.secret_key.encode(),
            prehash.encode(),
            hashlib.sha256,
        ).digest()
        sign_b64 = base64.b64encode(signature).decode()
        return {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": sign_b64,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
        }


def load_client_from_env() -> OkxClient:
    api_key = os.environ.get("OKX_API_KEY")
    secret_key = os.environ.get("OKX_SECRET_KEY")
    passphrase = os.environ.get("OKX_PASSPHRASE")
    base_url = os.environ.get("OKX_BASE_URL", "https://www.okx.com")

    if not all([api_key, secret_key, passphrase]):
        raise RuntimeError("Missing OKX credentials in environment variables.")

    return OkxClient(api_key=api_key, secret_key=secret_key, passphrase=passphrase, base_url=base_url)
