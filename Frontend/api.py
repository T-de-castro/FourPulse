import os
from concurrent.futures import ThreadPoolExecutor
from ipaddress import ip_address
from urllib.parse import urlsplit

import requests


API_BASE_URL = os.getenv("FOURPULSE_API_URL", "http://localhost:8000").rstrip("/")
_API_WORKERS = ThreadPoolExecutor(max_workers=5)


class APIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


def api_request(method, path, token=None, **kwargs):
    parsed_url = urlsplit(API_BASE_URL)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname:
        raise APIError("FOURPULSE_API_URL deve conter um endereço HTTP ou HTTPS válido.")
    if parsed_url.scheme == "http":
        try:
            local_host = parsed_url.hostname.casefold() == "localhost" or ip_address(
                parsed_url.hostname
            ).is_loopback
        except ValueError:
            local_host = False
        if not local_host:
            raise APIError("Use HTTPS ao conectar a uma API fora do computador local.")

    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.request(
            method,
            f"{API_BASE_URL}{path}",
            headers=headers,
            timeout=20,
            **kwargs,
        )
    except requests.RequestException as exc:
        raise APIError(
            f"Não foi possível conectar à API em {API_BASE_URL}: {exc}"
        ) from exc

    if not response.ok:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise APIError(str(detail), response.status_code)

    if response.status_code == 204 or not response.content:
        return None

    try:
        return response.json()
    except ValueError as exc:
        raise APIError("A API retornou uma resposta inválida.") from exc


def api_get_many(paths, token):
    futures = {
        path: _API_WORKERS.submit(api_request, "GET", path, token)
        for path in paths
    }
    return {path: future.result() for path, future in futures.items()}
