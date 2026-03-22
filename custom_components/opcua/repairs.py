from __future__ import annotations

from homeassistant.helpers import issue_registry as ir

from .const import (
    CONF_CLIENT_CERT_PATH,
    CONF_CLIENT_KEY_PATH,
    CONF_ENDPOINT,
    DOMAIN,
    ISSUE_MISSING_CERTIFICATE_FILES,
    SECURITY_POLICY_NONE,
)


def async_delete_repairs(hass, entry) -> None:
    """Delete repair issues for a config entry."""
    issue_id = f"{ISSUE_MISSING_CERTIFICATE_FILES}_{entry.entry_id}"
    ir.async_delete_issue(hass, DOMAIN, issue_id)


def async_sync_repairs(hass, entry) -> None:
    """Create or clear actionable repair issues for a config entry."""
    issue_id = f"{ISSUE_MISSING_CERTIFICATE_FILES}_{entry.entry_id}"
    security_policy = entry.data.get("security_policy", SECURITY_POLICY_NONE)
    client_cert_path = entry.data.get(CONF_CLIENT_CERT_PATH)
    client_key_path = entry.data.get(CONF_CLIENT_KEY_PATH)

    if security_policy != SECURITY_POLICY_NONE and (
        not client_cert_path or not client_key_path
    ):
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=True,
            is_persistent=True,
            severity=ir.IssueSeverity.ERROR,
            translation_key=ISSUE_MISSING_CERTIFICATE_FILES,
            translation_placeholders={
                "endpoint": str(entry.data.get(CONF_ENDPOINT, "unknown endpoint"))
            },
        )
        return

    ir.async_delete_issue(hass, DOMAIN, issue_id)
