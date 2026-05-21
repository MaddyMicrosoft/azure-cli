# Interactive `az login` E2E Tests

End-to-end tests that exercise the real interactive browser sign-in flow of
`az login` with **no mocking** of MSAL or Entra ID. A real headless Chromium
(driven by Playwright) fills in the AAD sign-in pages, redirects back to the
local listener started by `az login`, and the CLI exchanges the auth code for
a real token.

## Requirements

```pwsh
pip install playwright pytest
playwright install --with-deps chromium
```

## Required environment variables

| Variable | Purpose |
|---|---|
| `TEST_AAD_USER` | UPN of the dedicated test user (e.g. `cli-e2e@contoso.onmicrosoft.com`) |
| `TEST_AAD_PASSWORD` | Password for that user. Source from Key Vault, **never** commit. |
| `TEST_TENANT_ID` | Tenant GUID the user belongs to |

## Running locally

```pwsh
$env:TEST_AAD_USER      = "cli-e2e@contoso.onmicrosoft.com"
$env:TEST_AAD_PASSWORD  = "<from key vault>"
$env:TEST_TENANT_ID     = "00000000-0000-0000-0000-000000000000"

pytest src/azure-cli/azure/cli/command_modules/profile/tests/latest/e2e_interactive -v
```

## Safety notes

- Use a **dedicated test tenant / throwaway user** with zero real permissions.
- The fixture isolates `AZURE_CONFIG_DIR` to a temp folder so your real
  `~/.azure` cache is never touched.
- Do **not** publish raw `az login --debug` output or Playwright traces as
  pipeline artifacts; they can contain tokens.
- Disable WAM/broker so `az login` actually opens a browser:
  `az config set core.enable_broker_on_windows=false` (the fixture sets this
  for the isolated env automatically).
