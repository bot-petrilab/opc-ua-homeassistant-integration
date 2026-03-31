from __future__ import annotations

import asyncio
import logging
from collections import deque
from collections.abc import Awaitable, Callable
from typing import Any

from asyncua import Client, ua

from .const import (
    SECURITY_POLICY_BASIC256SHA256_SIGN,
    SECURITY_POLICY_BASIC256SHA256_SIGN_ENCRYPT,
    SECURITY_POLICY_NONE,
)
from .opcua_subscription import establish_subscription

_LOGGER = logging.getLogger(__name__)


class OpcUaClientManager:
    """Thin asyncua client wrapper with reconnect support."""

    def __init__(
        self,
        endpoint: str,
        security_policy: str,
        username: str | None,
        password: str | None,
        client_cert_path: str | None = None,
        client_key_path: str | None = None,
        server_cert_path: str | None = None,
        client_key_password: str | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.security_policy = security_policy
        self.username = username
        self.password = password
        self.client_cert_path = client_cert_path
        self.client_key_path = client_key_path
        self.server_cert_path = server_cert_path
        self.client_key_password = client_key_password

        self._client: Client | None = None
        self._subscription = None
        self._subscription_handles: list[Any] = []
        self._subscribed_node_ids: list[str] = []
        self._desired_subscription_node_ids: list[str] = []
        self._subscription_callback: (
            Callable[[str, Any], Awaitable[None] | None] | None
        ) = None
        self._lock = asyncio.Lock()

    async def ensure_connected(self) -> None:
        async with self._lock:
            if self._client is not None:
                return

            client = Client(self.endpoint)
            sec_retry_base: str | None = None

            if self.security_policy == SECURITY_POLICY_NONE:
                pass
            elif self.security_policy in {
                SECURITY_POLICY_BASIC256SHA256_SIGN,
                SECURITY_POLICY_BASIC256SHA256_SIGN_ENCRYPT,
            }:
                if not self.client_cert_path or not self.client_key_path:
                    raise ValueError(
                        "Security policy requires certificate + key paths "
                        "(client_cert_path/client_key_path)."
                    )

                mode = (
                    "Sign"
                    if self.security_policy == SECURITY_POLICY_BASIC256SHA256_SIGN
                    else "SignAndEncrypt"
                )

                sec_base = f"Basic256Sha256,{mode},{self.client_cert_path},{self.client_key_path}"
                sec_retry_base = sec_base

                # Primary attempt with optional server cert / key password.
                sec_candidates: list[str] = []
                sec_full = sec_base
                if self.server_cert_path:
                    sec_full += f",{self.server_cert_path}"
                if self.client_key_password:
                    sec_full += f",{self.client_key_password}"
                sec_candidates.append(sec_full)

                # Fallback: some asyncua/server combos reject/parse optional tail parameters differently.
                if sec_full != sec_base:
                    sec_candidates.append(sec_base)

                last_err: Exception | None = None
                for sec in sec_candidates:
                    try:
                        await client.set_security_string(sec)
                        last_err = None
                        break
                    except Exception as err:
                        last_err = err
                        _LOGGER.debug(
                            "set_security_string failed for candidate '%s': %s",
                            sec,
                            err,
                        )

                if last_err is not None:
                    raise last_err
            else:
                raise ValueError(f"Unsupported security policy: {self.security_policy}")

            if self.username:
                client.set_user(self.username)
            if self.password:
                client.set_password(self.password)

            try:
                await client.connect()
            except Exception as err:
                # Fallback for secure endpoints when optional server-cert tail caused compatibility issues.
                if sec_retry_base and self.server_cert_path:
                    _LOGGER.warning(
                        "Primary secure connect failed for %s, retrying without server_cert_path tail: %s",
                        self.endpoint,
                        err,
                    )
                    try:
                        await client.disconnect()
                    except Exception:
                        pass

                    retry_client = Client(self.endpoint)
                    await retry_client.set_security_string(sec_retry_base)
                    if self.username:
                        retry_client.set_user(self.username)
                    if self.password:
                        retry_client.set_password(self.password)
                    await retry_client.connect()
                    client = retry_client
                else:
                    raise

            self._client = client
            if self._desired_subscription_node_ids and self._subscription_callback:
                await self._establish_subscription(
                    self._desired_subscription_node_ids,
                    self._subscription_callback,
                )
            _LOGGER.info("Connected to OPC UA endpoint %s", self.endpoint)

    async def _clear_subscription(self, *, clear_desired: bool = False) -> None:
        if self._subscription is None:
            self._subscription_handles = []
            self._subscribed_node_ids = []
            if clear_desired:
                self._desired_subscription_node_ids = []
                self._subscription_callback = None
            return
        try:
            if self._subscription_handles:
                try:
                    await self._subscription.unsubscribe(self._subscription_handles)
                except Exception:
                    _LOGGER.debug("Error while unsubscribing OPC UA nodes", exc_info=True)
            try:
                await self._subscription.delete()
            except Exception:
                _LOGGER.debug("Error while deleting OPC UA subscription", exc_info=True)
        finally:
            self._subscription = None
            self._subscription_handles = []
            self._subscribed_node_ids = []
            if clear_desired:
                self._desired_subscription_node_ids = []
                self._subscription_callback = None

    async def disconnect(self, *, preserve_subscription: bool = False) -> None:
        async with self._lock:
            if self._client is None:
                return
            try:
                await self._clear_subscription(clear_desired=not preserve_subscription)
                await self._client.disconnect()
            except Exception:
                _LOGGER.debug("Error while disconnecting OPC UA client", exc_info=True)
            finally:
                self._client = None

    async def read_nodes(self, node_ids: list[str]) -> dict[str, Any]:
        """Read requested nodes with reconnect retry and per-node fault tolerance."""
        for attempt in range(2):
            try:
                await self.ensure_connected()
                assert self._client is not None

                result: dict[str, Any] = {}
                for node_id in node_ids:
                    try:
                        node = self._client.get_node(node_id)
                        result[node_id] = await node.read_value()
                    except Exception as node_err:
                        _LOGGER.debug(
                            "Node read failed %s on %s: %s",
                            node_id,
                            self.endpoint,
                            node_err,
                        )
                        result[node_id] = None
                return result
            except Exception as err:
                _LOGGER.warning(
                    "Read from OPC UA endpoint %s failed (attempt %s): %s",
                    self.endpoint,
                    attempt + 1,
                    err,
                )
                await self.disconnect(preserve_subscription=True)
                if attempt == 1:
                    raise

        return {node_id: None for node_id in node_ids}

    async def write_node(self, node_id: str, value: Any) -> None:
        """Write one node value with reconnect retry."""
        for attempt in range(2):
            try:
                await self.ensure_connected()
                assert self._client is not None

                node = self._client.get_node(node_id)
                await node.write_value(value)
                return
            except Exception as err:
                _LOGGER.warning(
                    "Write to OPC UA endpoint %s failed (attempt %s, node %s): %s",
                    self.endpoint,
                    attempt + 1,
                    node_id,
                    err,
                )
                await self.disconnect(preserve_subscription=True)
                if attempt == 1:
                    raise

    async def _establish_subscription(
        self,
        node_ids: list[str],
        callback: Callable[[str, Any], Awaitable[None] | None],
    ) -> None:
        assert self._client is not None
        await self._clear_subscription(clear_desired=False)
        subscription, handles, subscribed_node_ids = await establish_subscription(
            self._client, node_ids, callback, _LOGGER, self.endpoint
        )
        self._subscription = subscription
        self._subscription_handles = handles
        # Keep track of all requested node ids for reconnect/preservation semantics,
        # even if some individual subscribe calls failed.
        self._subscribed_node_ids = list(node_ids)

    async def subscribe_nodes(
        self,
        node_ids: list[str],
        callback: Callable[[str, Any], Awaitable[None] | None],
    ) -> dict[str, Any]:
        """Subscribe to node updates and return an initial snapshot."""
        uniq_node_ids = list(dict.fromkeys(node_ids))
        await self.ensure_connected()
        assert self._client is not None

        initial = await self.read_nodes(uniq_node_ids)
        self._desired_subscription_node_ids = uniq_node_ids
        self._subscription_callback = callback
        await self._establish_subscription(uniq_node_ids, callback)
        return initial

    async def browse_nodes(
        self,
        root_node_id: str = "i=85",
        depth: int | None = None,
        max_nodes: int | None = None,
    ) -> list[dict[str, Any]]:
        """Browse OPC-UA address space and return candidate nodes + metadata.

        Returned item fields can include:
        - node_id, name, node_class, path
        - is_writable, access_level
        - data_type, type_definition, sample_type
        - engineering_units, enum_strings
        """
        await self.ensure_connected()
        assert self._client is not None

        result: list[dict[str, Any]] = []
        visited: set[str] = set()

        queue: deque[tuple[str, int, str]] = deque()
        queue.append((root_node_id, 0, root_node_id))

        while queue and (max_nodes is None or len(result) < max_nodes):
            current_node_id, level, current_path = queue.popleft()
            if current_node_id in visited:
                continue
            visited.add(current_node_id)

            try:
                current_node = self._client.get_node(current_node_id)
                children = await current_node.get_children()
            except Exception as err:
                _LOGGER.debug("Browse failed for node %s: %s", current_node_id, err)
                continue

            for child in children:
                try:
                    node_id_obj = child.nodeid
                    child_node_id = (
                        node_id_obj.to_string()
                        if hasattr(node_id_obj, "to_string")
                        else str(node_id_obj)
                    )

                    browse_name = await child.read_browse_name()
                    name = getattr(browse_name, "Name", str(browse_name))

                    node_class_obj = await child.read_node_class()
                    node_class = getattr(node_class_obj, "name", str(node_class_obj))

                    child_path = f"{current_path}/{name}"
                    item: dict[str, Any] = {
                        "node_id": child_node_id,
                        "name": str(name),
                        "node_class": str(node_class),
                        "path": child_path,
                        "parent_node_id": current_node_id,
                        "level": level + 1,
                    }

                    # Type definition can be useful for Object and Variable discovery.
                    try:
                        type_def = await child.read_type_definition()
                        item["type_definition"] = (
                            type_def.to_string()
                            if hasattr(type_def, "to_string")
                            else str(type_def)
                        )
                    except Exception:
                        pass

                    if str(node_class) == "Variable":
                        # Access / writable
                        try:
                            attr = await child.read_attribute(
                                ua.AttributeIds.AccessLevel
                            )
                            access_level = int(attr.Value.Value)
                            item["access_level"] = access_level
                            item["is_writable"] = bool(access_level & 0x02)
                        except Exception:
                            item["is_writable"] = False

                        # Data type
                        try:
                            data_type = await child.read_data_type()
                            item["data_type"] = (
                                data_type.to_string()
                                if hasattr(data_type, "to_string")
                                else str(data_type)
                            )
                        except Exception:
                            pass

                        # Sample type/value (scalar sample_value helps higher-level discovery)
                        try:
                            sample_value = await child.read_value()
                            item["sample_type"] = type(sample_value).__name__
                            if (
                                isinstance(sample_value, (bool, int, float, str))
                                or sample_value is None
                            ):
                                item["sample_value"] = sample_value
                        except Exception:
                            pass

                        # Optional companion-ish metadata from properties
                        try:
                            props = await child.get_properties()
                            for prop in props:
                                try:
                                    prop_bn = await prop.read_browse_name()
                                    prop_name = str(getattr(prop_bn, "Name", prop_bn))
                                    if prop_name == "EngineeringUnits":
                                        eng = await prop.read_value()
                                        item["engineering_units"] = str(eng)
                                    elif prop_name == "EnumStrings":
                                        enum_vals = await prop.read_value()
                                        item["enum_strings"] = [
                                            str(x) for x in list(enum_vals)[:32]
                                        ]
                                except Exception:
                                    continue
                        except Exception:
                            pass

                    result.append(item)

                    if (
                        depth is None or level + 1 < depth
                    ) and child_node_id not in visited:
                        queue.append((child_node_id, level + 1, child_path))

                    if max_nodes is not None and len(result) >= max_nodes:
                        break
                except Exception as err:
                    _LOGGER.debug(
                        "Browse child parse failed under %s: %s", current_node_id, err
                    )

        return result

    @staticmethod
    def _security_policy_short(policy_uri: str) -> str:
        if "#" in policy_uri:
            return policy_uri.split("#", 1)[1]
        return policy_uri.rsplit("/", 1)[-1]

    @staticmethod
    async def discover_servers(
        discovery_url: str,
        include_network: bool = False,
    ) -> list[dict[str, Any]]:
        """Discover available OPC-UA servers and endpoints from a discovery URL."""
        discovered: list[dict[str, Any]] = []

        async def _safe_disconnect(client: Client) -> None:
            try:
                await client.disconnect()
            except Exception:
                pass

        probe = Client(discovery_url)
        app_rows = []
        endpoint_rows = []
        network_rows = []

        try:
            app_rows = await probe.connect_and_find_servers()
        except Exception as err:
            _LOGGER.debug("FindServers failed on %s: %s", discovery_url, err)
        finally:
            await _safe_disconnect(probe)

        probe_eps = Client(discovery_url)
        try:
            endpoint_rows = await probe_eps.connect_and_get_server_endpoints()
        except Exception as err:
            _LOGGER.debug("GetEndpoints failed on %s: %s", discovery_url, err)
        finally:
            await _safe_disconnect(probe_eps)

        if include_network:
            probe_net = Client(discovery_url)
            try:
                network_rows = await probe_net.connect_and_find_servers_on_network()
            except Exception as err:
                _LOGGER.debug(
                    "FindServersOnNetwork failed on %s: %s", discovery_url, err
                )
            finally:
                await _safe_disconnect(probe_net)

        app_discovery_urls: list[str] = []
        for app in app_rows:
            for u in list(getattr(app, "DiscoveryUrls", []) or []):
                if isinstance(u, str) and u.startswith("opc.tcp://"):
                    app_discovery_urls.append(u)

        network_discovery_urls: list[str] = []
        for row in network_rows:
            one_url = getattr(row, "DiscoveryUrl", None)
            if isinstance(one_url, str) and one_url.startswith("opc.tcp://"):
                network_discovery_urls.append(one_url)

            many_urls = getattr(row, "DiscoveryUrls", []) or []
            if isinstance(many_urls, (list, tuple)):
                for u in many_urls:
                    if isinstance(u, str) and u.startswith("opc.tcp://"):
                        network_discovery_urls.append(u)

        discovery_urls = [discovery_url] + app_discovery_urls + network_discovery_urls
        seen_urls: set[str] = set()
        uniq_discovery_urls: list[str] = []
        for u in discovery_urls:
            if u in seen_urls:
                continue
            seen_urls.add(u)
            uniq_discovery_urls.append(u)

        all_endpoint_rows: list[tuple[str, Any]] = []
        for ep in endpoint_rows:
            all_endpoint_rows.append((discovery_url, ep))

        for u in uniq_discovery_urls:
            if u == discovery_url:
                continue
            c = Client(u)
            try:
                rows = await c.connect_and_get_server_endpoints()
                for ep in rows:
                    all_endpoint_rows.append((u, ep))
            except Exception as err:
                _LOGGER.debug("GetEndpoints failed on discovered URL %s: %s", u, err)
            finally:
                await _safe_disconnect(c)

        app_meta: dict[str, dict[str, Any]] = {}
        for app in app_rows:
            app_uri = str(getattr(app, "ApplicationUri", ""))
            app_meta[app_uri] = {
                "application_uri": app_uri,
                "application_name": str(
                    getattr(getattr(app, "ApplicationName", None), "Text", "")
                ),
                "product_uri": str(getattr(app, "ProductUri", "")),
                "discovery_urls": list(getattr(app, "DiscoveryUrls", []) or []),
            }

        seen_endpoint_keys: set[str] = set()
        for src_url, ep in all_endpoint_rows:
            try:
                endpoint_url = str(getattr(ep, "EndpointUrl", ""))
                if not endpoint_url:
                    continue

                policy_uri = str(getattr(ep, "SecurityPolicyUri", ""))
                policy_short = OpcUaClientManager._security_policy_short(policy_uri)
                security_mode_obj = getattr(ep, "SecurityMode", None)
                security_mode_name = getattr(
                    security_mode_obj, "name", str(security_mode_obj)
                )
                security_level = int(getattr(ep, "SecurityLevel", 0) or 0)
                transport = str(getattr(ep, "TransportProfileUri", ""))

                app_desc = getattr(ep, "Server", None)
                app_uri = str(getattr(app_desc, "ApplicationUri", ""))
                app_name = str(
                    getattr(getattr(app_desc, "ApplicationName", None), "Text", "")
                )

                if app_uri in app_meta:
                    app_name = app_meta[app_uri].get("application_name") or app_name

                key = f"{endpoint_url}|{policy_uri}|{security_mode_name}"
                if key in seen_endpoint_keys:
                    continue
                seen_endpoint_keys.add(key)

                supported_now = policy_short == "None" or (
                    policy_short == "Basic256Sha256"
                    and security_mode_name in {"Sign", "SignAndEncrypt"}
                )

                discovered.append(
                    {
                        "source_discovery_url": src_url,
                        "endpoint_url": endpoint_url,
                        "security_policy_uri": policy_uri,
                        "security_policy": policy_short,
                        "security_mode": security_mode_name,
                        "security_level": security_level,
                        "transport_profile_uri": transport,
                        "application_uri": app_uri,
                        "application_name": app_name,
                        "supported_now": supported_now,
                    }
                )
            except Exception as err:
                _LOGGER.debug("Endpoint mapping failed: %s", err)

        return discovered
