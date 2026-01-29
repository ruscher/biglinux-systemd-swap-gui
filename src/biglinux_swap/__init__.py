"""
BigLinux Swap Manager - GTK4/Adwaita GUI for systemd-swap.

This package provides a graphical interface for configuring
systemd-swap on BigLinux systems.

Usage:
    # From installed package
    python -m biglinux_swap

    # Direct execution (development)
    cd src/biglinux_swap
    python __init__.py
"""

import sys
from pathlib import Path

__version__ = "1.0.0"
__author__ = "BigLinux Team"
__license__ = "GPL-3.0"

# Support direct execution without installation
# Add parent directory to path so imports work
_current_file = Path(__file__).resolve()
_package_dir = _current_file.parent
_src_dir = _package_dir.parent

if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from biglinux_swap.application import SwapApplication
from biglinux_swap.config import (
    APP_ID,
    APP_NAME,
    APP_VERSION,
    Compressor,
    MglruTtl,
    SwapConfig,
    SwapFileConfig,
    SwapMode,
    ZramConfig,
    ZswapConfig,
)
from biglinux_swap.main import main

__all__ = [
    "APP_ID",
    "APP_NAME",
    "APP_VERSION",
    "Compressor",
    "MglruTtl",
    "SwapApplication",
    "SwapConfig",
    "SwapFileConfig",
    "SwapMode",
    "ZramConfig",
    "ZswapConfig",
    "main",
    "__version__",
]


if __name__ == "__main__":
    sys.exit(main())
