"""Local browser backend connects to Chrome via CDP.

Connects to a user's already-running Chrome instance via the Chrome
DevTools Protocol (CDP) on a configurable port.  All existing cookies,
logins, and sessions in that browser are immediately available no
``session_data`` or authentication code needed.

Before using this backend, either:

1. Start Chrome manually::

       google-chrome \\
           --remote-debugging-port=9222 \\
           --user-data-dir="$HOME/.config/google-chrome-debug" \\
           --profile-directory="Default"

2. Or let the backend auto-launch Chrome (it will attempt to find and
   start Chrome with the debug profile if the port is not already open).

Important:
    The debug profile at ``~/.config/google-chrome-debug`` is separate
    from your default Chrome profile.  You must log into target sites
    (e.g. LinkedIn) in this profile *before* scraping.  Use::

        make chrome-debug-login URL=https://www.linkedin.com

    to open Chrome with this profile and log in.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from typing import TYPE_CHECKING

from intelliscraper.browser.backend import BrowserBackend
from intelliscraper.exception import LocalBrowserConnectionError

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Playwright

logger = logging.getLogger(__name__)

# CDP connection constants.
_CDP_DEFAULT_PORT = 9222
_CDP_MAX_WAIT_SEC = 20
_CDP_POLL_INTERVAL_SEC = 1.0
_CDP_CONNECT_TIMEOUT_MS = 10_000


class LocalBrowserBackend(BrowserBackend):
    """Connect to an already-running Chrome instance via CDP.

    This backend reuses the user's real Chrome session, preserving all
    cookies, localStorage, and authenticated state.  It is ideal for
    scraping sites that require complex authentication flows (e.g.
    LinkedIn, Gmail).

    Args:
        cdp_port: Chrome DevTools Protocol port.  Defaults to 9222.
        headless: If Chrome needs to be auto-launched, whether to run it
            headless.  Defaults to ``True``.
        profile_dir: Path to the Chrome user-data-dir used for the debug
            profile.  Defaults to ``~/.config/google-chrome-debug``.

    Raises:
        LocalBrowserConnectionError: If Chrome is not reachable after
            ``_CDP_MAX_WAIT_SEC`` seconds.

    Example::

        backend = LocalBrowserBackend(cdp_port=9222, headless=False)
        browser, context = await backend.initialize(playwright)
    """

    def __init__(
        self,
        cdp_port: int = _CDP_DEFAULT_PORT,
        headless: bool = True,
        profile_dir: str | None = None,
    ) -> None:
        self._cdp_port = cdp_port
        self._cdp_url = f"http://localhost:{cdp_port}"
        self._headless = headless
        self._profile_dir = profile_dir or os.path.join(
            os.path.expanduser("~"), ".config", "google-chrome-debug"
        )

    # BrowserBackend interface

    @property
    def owns_browser(self) -> bool:
        """Local backend does not own the browser process."""
        return False

    async def initialize(
        self,
        playwright: Playwright,
    ) -> tuple[Browser, BrowserContext]:
        """Connect to Chrome via CDP and return browser + context.

        If Chrome is not already running on the configured port, the
        backend will attempt to auto-launch it using the debug profile.

        Args:
            playwright: A started Playwright instance.

        Returns:
            A ``(browser, context)`` tuple.  The context is the first
            existing context found in the CDP browser (preserving all
            cookies and logins).

        Raises:
            LocalBrowserConnectionError: If Chrome cannot be reached.
        """

        logger.info("Checking Chrome debug port at %s ...", self._cdp_url)

        # Fast pre-check: is Chrome already up?
        if not self._is_chrome_port_open():
            logger.info(
                "Chrome debug port not detected attempting to launch "
                "Chrome with remote debugging enabled ..."
            )
            await self._launch_chrome_with_debugging()
            logger.info(
                "Waiting up to %ds for Chrome to be ready ...",
                _CDP_MAX_WAIT_SEC,
            )

        # Poll until Chrome is reachable.
        reachable = await self._wait_for_chrome_port()
        if not reachable:
            raise LocalBrowserConnectionError(
                f"Chrome not reachable on port {self._cdp_port} after "
                f"{_CDP_MAX_WAIT_SEC}s.\n\n"
                "Please start Chrome manually with remote debugging:\n\n"
                "  google-chrome \\\n"
                "    --remote-debugging-port=9222 \\\n"
                '    --user-data-dir="$HOME/.config/google-chrome-debug" \\\n'
                '    --profile-directory="Default"\n\n'
                "Or use:  make chrome-debug-login URL=https://example.com\n\n"
                "Note: all existing Chrome windows must be FULLY closed "
                "first, then run the command above before using "
                "IntelliScraper."
            )

        # Connect over CDP.
        logger.info("Connecting to Chrome via CDP ...")
        try:
            browser = await playwright.chromium.connect_over_cdp(
                endpoint_url=self._cdp_url,
                timeout=_CDP_CONNECT_TIMEOUT_MS,
            )
        except Exception as exc:
            raise LocalBrowserConnectionError(
                f"Chrome is reachable at {self._cdp_url} but CDP "
                f"connection failed.\nError: {exc}"
            ) from exc

        # Reuse existing context (preserves all logins / cookies).
        if browser.contexts:
            context = browser.contexts[0]
            logger.info(
                "Reusing existing browser context (%d context(s) found)",
                len(browser.contexts),
            )
        else:
            logger.warning(
                "No existing context found in CDP browser — creating a "
                "fresh one.  You may need to log in to target sites "
                "manually."
            )
            context = await browser.new_context(ignore_https_errors=True)

        logger.info("Local browser (CDP) ready.")
        return browser, context

    async def cleanup(
        self,
        browser: Browser,
        context: BrowserContext,
    ) -> None:
        """Clean up local browser resources.

        In CDP mode the Chrome process and context belong to the user,
        so they are **not** closed.  Only a debug log entry is emitted.

        Args:
            browser: The CDP-connected browser (not closed).
            context: The reused browser context (not closed).
        """
        logger.debug(
            "CDP mode: skipping context/browser close "
            "(Chrome instance belongs to user)"
        )

    def _is_chrome_port_open(self) -> bool:
        """Return ``True`` if the Chrome debug port already responds.

        Performs a single synchronous HTTP probe against
        ``/json/version`` with a 2-second timeout.
        """
        try:
            urllib.request.urlopen(f"{self._cdp_url}/json/version", timeout=2)
            return True
        except Exception:
            return False

    async def _launch_chrome_with_debugging(self) -> None:
        """Launch Chrome with remote debugging using the debug profile.

        Searches for a Chrome/Chromium executable, kills any existing
        Chrome processes that might hold the profile lock, then launches
        Chrome with the required flags.

        Note:
            ``pkill`` targets ``/opt/google/chrome/chrome`` specifically
            to avoid killing Electron-based apps (e.g. VS Code).
        """
        chrome_executables = [
            "google-chrome",
            "google-chrome-stable",
            "chromium-browser",
            "chromium",
        ]
        chrome_bin = next(
            (exe for exe in chrome_executables if shutil.which(exe)),
            None,
        )
        if chrome_bin is None:
            logger.warning(
                "Could not find a Chrome/Chromium executable.  Please "
                "start Chrome manually with "
                "--remote-debugging-port=9222."
            )
            return

        # Kill existing Chrome processes to unlock the profile.
        logger.info(
            "Terminating existing Chrome processes to unlock the " "debug profile ..."
        )
        try:
            subprocess.run(
                ["pkill", "-f", "google-chrome-debu[g]"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                ["pkill", "-f", "chromium-browser.*debu[g]"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            await asyncio.sleep(2)
        except Exception as exc:
            logger.warning(
                "Could not kill Chrome processes: %s.  Proceeding anyway.",
                exc,
            )

        cmd = [
            chrome_bin,
            f"--remote-debugging-port={self._cdp_port}",
            f"--user-data-dir={self._profile_dir}",
            "--profile-directory=Default",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
        ]

        if self._headless:
            cmd.append("--headless=new")

        env = os.environ.copy()
        env.setdefault("DISPLAY", ":0")

        headless_msg = "headless" if self._headless else "visible"
        logger.info(
            "Auto-launching Chrome (%s, profile: %s).\n"
            "  NOTE: This uses the debug profile.  Log into target "
            "sites in this profile before scraping.",
            headless_msg,
            self._profile_dir,
        )
        logger.debug("Chrome command: %s", " ".join(cmd))

        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env=env,
        )

    async def _wait_for_chrome_port(self) -> bool:
        """Poll Chrome's debug endpoint until it responds or timeout.

        Probes ``/json/version`` once per ``_CDP_POLL_INTERVAL_SEC``
        seconds, up to ``_CDP_MAX_WAIT_SEC`` total.

        Returns:
            ``True`` if Chrome responded within the timeout.
        """
        max_attempts = int(_CDP_MAX_WAIT_SEC / _CDP_POLL_INTERVAL_SEC)
        for attempt in range(max_attempts):
            try:
                urllib.request.urlopen(f"{self._cdp_url}/json/version", timeout=2)
                logger.debug(
                    "Chrome port reachable after ~%.0fs",
                    attempt * _CDP_POLL_INTERVAL_SEC,
                )
                return True
            except Exception:
                logger.debug(
                    "Port not ready yet — attempt %d/%d",
                    attempt + 1,
                    max_attempts,
                )
                await asyncio.sleep(_CDP_POLL_INTERVAL_SEC)
        return False
