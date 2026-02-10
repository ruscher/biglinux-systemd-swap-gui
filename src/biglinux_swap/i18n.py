"""Internationalization setup for BigLinux Swap Manager."""

from __future__ import annotations

import contextlib
import gettext
import locale
from pathlib import Path

LOCALE_DIR = Path("/usr/share/locale")
DOMAIN = "biglinux-swap"

with contextlib.suppress(locale.Error):
    locale.setlocale(locale.LC_ALL, "")

try:
    translation = gettext.translation(DOMAIN, LOCALE_DIR, fallback=True)
    _ = translation.gettext
except Exception:

    def _(text: str) -> str:
        return text
