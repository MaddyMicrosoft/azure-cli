"""End-to-end test for `az login` via the real interactive browser flow.

This test does NOT mock MSAL, Entra ID, or the CLI. It:
  1. Launches `az login --debug` in a subprocess with an isolated config dir.
  2. Scrapes the OAuth authorize URL from the CLI's debug output.
  3. Drives the AAD sign-in pages with headless Chromium (Playwright).
  4. Lets the CLI complete the localhost redirect + token exchange.
  5. Verifies `az account show` reports the expected user and tenant.
"""
from __future__ import annotations

import json
import subprocess
import sys

import pytest

from helpers.az_runner import start_az_login
from helpers.browser_driver import complete_aad_login


@pytest.mark.e2e
def test_interactive_login_end_to_end(isolated_az_config, aad_credentials):
    env = isolated_az_config
    creds = aad_credentials

    proc, auth_url = start_az_login(env)

    try:
        complete_aad_login(
            auth_url,
            username=creds["user"],
            password=creds["password"],
            headless=False,
        )
        exit_code = proc.wait(timeout=180)
    except Exception:
        proc.kill()
        raise

    assert exit_code == 0, (
        f"az login exited with {exit_code}. "
        f"stderr tail: {proc.stderr.read()[-2000:] if proc.stderr else ''}"
    )

    result = subprocess.run(
        ["az", "account", "show"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
        shell=sys.platform == "win32",
    )
    acct = json.loads(result.stdout)

    assert acct["user"]["name"].lower() == creds["user"].lower()

    # Cleanly log out so the temp cache is also empty before teardown.
    subprocess.run(
        ["az", "logout"],
        env=env,
        check=False,
        shell=sys.platform == "win32",
    )
