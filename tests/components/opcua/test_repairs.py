from types import SimpleNamespace

from custom_components.opcua.repairs import async_delete_repairs, async_sync_repairs


def test_repairs_create_issue_for_secure_policy_without_cert_files() -> None:
    hass = SimpleNamespace()
    entry = SimpleNamespace(
        entry_id="entry-1",
        data={
            "endpoint": "opc.tcp://host:4840",
            "security_policy": "Basic256Sha256_SignAndEncrypt",
            "client_cert_path": "",
            "client_key_path": "",
        },
    )

    async_sync_repairs(hass, entry)

    assert len(hass._issues) == 1
    domain, issue_id, payload = hass._issues[0]
    assert domain == "opcua"
    assert issue_id == "missing_certificate_files_entry-1"
    assert payload["translation_key"] == "missing_certificate_files"
    assert payload["translation_placeholders"]["endpoint"] == "opc.tcp://host:4840"


def test_repairs_delete_issue_when_config_is_valid_or_unloaded() -> None:
    hass = SimpleNamespace(_issues=[("opcua", "missing_certificate_files_entry-1", {"x": 1})])
    entry = SimpleNamespace(
        entry_id="entry-1",
        data={
            "endpoint": "opc.tcp://host:4840",
            "security_policy": "Basic256Sha256_SignAndEncrypt",
            "client_cert_path": "/config/cert.pem",
            "client_key_path": "/config/key.pem",
        },
    )

    async_sync_repairs(hass, entry)
    assert hass._issues == []

    hass._issues = [("opcua", "missing_certificate_files_entry-1", {"x": 1})]
    async_delete_repairs(hass, entry)
    assert hass._issues == []
