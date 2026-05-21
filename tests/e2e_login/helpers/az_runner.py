"""Launch `az login` as a subprocess and capture the OAuth auth URL.

The CLI normally opens the system browser to the Microsoft sign-in page. We
suppress that by passing `--debug` (which logs the URL to stderr) and
intercepting the URL before a browser would ever be useful. Playwright then
drives the sign-in headlessly.
"""
from __future__ import annotations

import queue
import re
import subprocess
import sys
import threading
from typing import Tuple

# Matches the full OAuth authorize URL printed by MSAL in debug logs.
_AUTH_URL_RE = re.compile(r"(https://login\.microsoftonline\.com/\S+)")


def start_az_login(env: dict, extra_args: list | None = None,
                   url_timeout: float = 30.0) -> Tuple[subprocess.Popen, str]:
    """Start `az login --debug` and return (process, auth_url).

    A background thread reads stderr until it finds the authorize URL
    (identified by the presence of `response_type=` in the query string) and
    puts it on a queue. The main thread blocks on the queue with a timeout.
    """
    args = ["az", "login", "--debug"]
    if extra_args:
        args.extend(extra_args)

    # On Windows, `az` is a .cmd shim; shell=False + the full name works on
    # all OSes when az is on PATH.
    proc = subprocess.Popen(
        args,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        shell=sys.platform == "win32",
    )

    url_q: "queue.Queue[str]" = queue.Queue()

    def _reader() -> None:
        try:
            for line in proc.stderr:  # type: ignore[arg-type]
                m = _AUTH_URL_RE.search(line)
                if m and "response_type" in m.group(1):
                    url_q.put(m.group(1))
                    return
        except Exception:  # pragma: no cover - defensive
            pass

    t = threading.Thread(target=_reader, daemon=True)
    t.start()

    try:
        auth_url = url_q.get(timeout=url_timeout)
    except queue.Empty as ex:
        proc.kill()
        raise RuntimeError(
            f"Did not see an OAuth auth URL within {url_timeout}s. "
            "Is `az` on PATH and is the broker disabled?"
        ) from ex

    return proc, auth_url
