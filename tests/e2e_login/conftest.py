"""Pytest fixtures for interactive `az login` E2E tests.

The key fixture is `isolated_az_config`, which gives each test a fresh
`AZURE_CONFIG_DIR` so tokens and subscription state never touch the
developer's real `~/.azure` directory. We also force-disable the Windows
broker (WAM) so `az login` actually opens a browser (which Playwright can
drive) rather than a native OS dialog (which it cannot).
"""
from __future__ import annotations

import os
import shutil
import tempfile

import pytest


@pytest.fixture
def isolated_az_config():
    """Yield an env dict pointing AZURE_CONFIG_DIR at a fresh temp folder."""
    config_dir = tempfile.mkdtemp(prefix="aztest-")
    env = os.environ.copy()
    env["AZURE_CONFIG_DIR"] = config_dir
    # Force browser flow (not WAM/broker) so Playwright can drive sign-in.
    env["AZURE_CORE_ENABLE_BROKER_ON_WINDOWS"] = "false"
    try:
        yield env
    finally:
        shutil.rmtree(config_dir, ignore_errors=True)


@pytest.fixture
def aad_credentials():
    """Read test credentials from env. Skip the test if they're missing.

    Returned as a ``_Creds`` object whose ``repr`` redacts the password so it
    cannot leak into pytest failure output, CI logs, or screenshots.
    """
    user = os.environ.get("TEST_AAD_USER")
    password = os.environ.get("TEST_AAD_PASSWORD")
    tenant = os.environ.get("TEST_TENANT_ID")
    if not (user and password and tenant):
        pytest.skip(
            "TEST_AAD_USER / TEST_AAD_PASSWORD / TEST_TENANT_ID not set; "
            "skipping interactive login E2E."
        )

    class _Creds:
        def __init__(self, u, p, t):
            self.user, self.password, self.tenant = u, p, t

        def __getitem__(self, k):  # backward-compat dict access
            return {"user": self.user, "password": self.password,
                    "tenant": self.tenant}[k]

        def __repr__(self):
            return f"<Creds user={self.user} tenant={self.tenant} password=***>"

    return _Creds(user, password, tenant)
