from pathlib import Path

from forgeloop.credentials.store import CredentialStore


def test_encrypted_file_creds(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("FORGELOOP_API_KEY", raising=False)
    store = CredentialStore(
        file_path=tmp_path / "secrets.enc",
        master_password="test-master-pass",
        force_file=True,
    )
    backend = store.set_key("sk-test-secret-key-1234")
    assert backend == "encrypted_file"
    st = store.status()
    assert st.configured
    assert st.backend == "encrypted_file"
    assert "sk-test" not in st.hint_mask
    assert st.hint_mask.endswith("1234")
    assert store.get_key() == "sk-test-secret-key-1234"
    store.clear()
    assert store.get_key() is None
