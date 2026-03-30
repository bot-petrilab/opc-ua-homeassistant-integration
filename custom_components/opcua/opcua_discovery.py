from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

from asyncua import Client

from .const import SECURITY_POLICY_NONE

_LOGGER = logging.getLogger(__name__)


def build_discovered_endpoint(endpoint, include_network: bool) -> dict[str, Any] | None:
    """Map an asyncua endpoint description to a stable dict."""
    try:
        ep_url = endpoint.EndpointUrl
        sec_uri = endpoint.SecurityPolicyUri or ""
        sec_name = sec_uri.rsplit("/", 1)[-1] if "/" in sec_uri else sec_uri
        sec_mode = getattr(endpoint.SecurityMode, "name", str(endpoint.SecurityMode))
        sec_level = int(getattr(endpoint, "SecurityLevel", 0) or 0)
        transport = getattr(endpoint, "TransportProfileUri", None)
        server = getattr(endpoint, "Server", None)
        app_uri = getattr(server, "ApplicationUri", None) if server else None
        app_name_obj = getattr(server, "ApplicationName", None) if server else None
        app_name = getattr(app_name_obj, "Text", None) if app_name_obj else None
        hostname = ""
        if include_network:
            parsed = urlparse(ep_url)
            hostname = parsed.hostname or ""
        supported_now = sec_name in {SECURITY_POLICY_NONE, "Basic256Sha256"}
        return {
            "endpoint_url": ep_url,
            "security_policy": sec_name,
            "security_mode": sec_mode,
            "security_level": sec_level,
            "transport_profile_uri": transport,
            "application_uri": app_uri,
            "application_name": app_name,
            "hostname": hostname,
            "supported_now": supported_now,
        }
    except Exception as err:
        _LOGGER.debug("Endpoint mapping failed: %s", err)
        return None


async def discover_servers(discovery_url: str, include_network: bool) -> list[dict[str, Any]]:
    """Discover endpoints via GetEndpoints on a discovery URL."""
    client = Client(url=discovery_url)
    try:
        endpoints = await client.connect_and_get_server_endpoints()
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass

    discovered: list[dict[str, Any]] = []
    for endpoint in endpoints:
        mapped = build_discovered_endpoint(endpoint, include_network)
        if mapped is not None:
            discovered.append(mapped)
    return discovered
