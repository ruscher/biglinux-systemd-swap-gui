#!/usr/bin/env python3
"""
Module entry point for BigLinux Swap Manager.

Enables execution via: python -m biglinux_swap
"""

from biglinux_swap.main import main

if __name__ == "__main__":
    raise SystemExit(main())
