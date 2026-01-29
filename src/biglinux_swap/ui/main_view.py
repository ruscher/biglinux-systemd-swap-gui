#!/usr/bin/env python3
"""
Main view for BigLinux Swap Manager.

Displays system status including memory usage chart and swap statistics.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk

from biglinux_swap.config import CHART_UPDATE_INTERVAL_MS
from biglinux_swap.services import MemoryStats, ServiceState
from biglinux_swap.ui.components import (
    create_action_button,
    create_preferences_group,
    create_status_indicator,
    create_status_row,
    update_status_row,
)
from biglinux_swap.ui.memory_chart import MemoryBarsWidget, MemoryChartWidget

if TYPE_CHECKING:
    from biglinux_swap.services import ConfigService, MeminfoService, SwapService

logger = logging.getLogger(__name__)


class MainView(Adw.NavigationPage):
    """
    Main view displaying system status and swap information.

    Contains:
    - Memory usage chart
    - Service status
    - Zswap statistics
    - Zram statistics
    - SwapFile statistics
    - Settings navigation button
    """

    def __init__(
        self,
        config_service: ConfigService,
        swap_service: SwapService,
        meminfo_service: MeminfoService,
        on_toast: Callable[[str, int], None] | None = None,
        on_navigate_settings: Callable[[], None] | None = None,
        on_apply: Callable[[], None] | None = None,
    ) -> None:
        """
        Initialize the main view.

        Args:
            config_service: Configuration service
            swap_service: Swap status service
            meminfo_service: Memory info service
            on_toast: Callback for toast notifications
            on_navigate_settings: Callback to navigate to settings
            on_apply: Callback to apply configuration changes
        """
        super().__init__(title="Swap Manager", tag="main")

        self._config_service = config_service
        self._swap_service = swap_service
        self._meminfo_service = meminfo_service
        self._on_toast = on_toast
        self._on_navigate_settings = on_navigate_settings
        self._on_apply = on_apply

        # Widget references
        self._chart: MemoryChartWidget | None = None
        self._bars: MemoryBarsWidget | None = None
        self._status_indicator: Gtk.Box | None = None
        self._mode_row: Adw.ActionRow | None = None

        # Zswap status rows
        self._zswap_group: Adw.PreferencesGroup | None = None
        self._zswap_compressor_row: Adw.ActionRow | None = None
        self._zswap_pool_row: Adw.ActionRow | None = None
        self._zswap_stored_row: Adw.ActionRow | None = None
        self._zswap_ratio_row: Adw.ActionRow | None = None

        # Zram status rows
        self._zram_group: Adw.PreferencesGroup | None = None
        self._zram_size_row: Adw.ActionRow | None = None

        # SwapFile status rows
        self._swapfile_group: Adw.PreferencesGroup | None = None
        self._swapfile_files_row: Adw.ActionRow | None = None
        self._swapfile_size_row: Adw.ActionRow | None = None

        # Update timer
        self._status_timer: int = 0

        self._setup_ui()
        self._start_monitoring()

    def _setup_ui(self) -> None:
        """Set up the UI layout."""
        # Scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)

        # Clamp for content width
        clamp = Adw.Clamp()
        clamp.set_maximum_size(600)
        clamp.set_margin_top(12)
        clamp.set_margin_bottom(24)
        clamp.set_margin_start(12)
        clamp.set_margin_end(12)

        # Main content box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)

        # === Memory Chart Section ===
        chart_group = create_preferences_group(
            "Memory Usage",
            "Real-time memory and swap usage (last 60 seconds)",
        )

        # Chart widget
        self._chart = MemoryChartWidget()
        chart_group.add(self._chart)

        # Memory bars below chart
        self._bars = MemoryBarsWidget()
        chart_group.add(self._bars)

        main_box.append(chart_group)

        # === Service Status Section ===
        status_group = create_preferences_group("Service Status")

        # Service state row
        self._status_row = create_status_row(
            "systemd-swap",
            "Checking...",
            icon_name="system-run-symbolic",
        )
        self._status_indicator = create_status_indicator(False, "")
        self._status_row.add_suffix(self._status_indicator)
        status_group.add(self._status_row)

        # Mode row
        self._mode_row = create_status_row(
            "Mode",
            "...",
            icon_name="emblem-system-symbolic",
        )
        status_group.add(self._mode_row)

        main_box.append(status_group)

        # === Zswap Section ===
        self._zswap_group = create_preferences_group(
            "Zswap",
            "Compressed RAM cache for swap pages",
        )

        self._zswap_compressor_row = create_status_row("Compressor", "-")
        self._zswap_group.add(self._zswap_compressor_row)

        self._zswap_pool_row = create_status_row("Pool Size", "-")
        self._zswap_group.add(self._zswap_pool_row)

        self._zswap_stored_row = create_status_row("Stored Data", "-")
        self._zswap_group.add(self._zswap_stored_row)

        self._zswap_ratio_row = create_status_row("Compression Ratio", "-")
        self._zswap_group.add(self._zswap_ratio_row)

        main_box.append(self._zswap_group)

        # === Zram Section ===
        self._zram_group = create_preferences_group(
            "Zram",
            "Compressed block device in RAM",
        )

        self._zram_size_row = create_status_row("Size", "-")
        self._zram_group.add(self._zram_size_row)

        main_box.append(self._zram_group)

        # === SwapFile Section ===
        self._swapfile_group = create_preferences_group(
            "SwapFile",
            "Dynamic swap files",
        )

        self._swapfile_files_row = create_status_row("Swap Files", "-")
        self._swapfile_group.add(self._swapfile_files_row)

        self._swapfile_size_row = create_status_row("Total Size", "-")
        self._swapfile_group.add(self._swapfile_size_row)

        main_box.append(self._swapfile_group)

        # === Action Buttons ===
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(12)

        # Settings button
        settings_btn = create_action_button(
            "Settings",
            icon_name="preferences-system-symbolic",
            style="",
            on_clicked=self._on_settings_clicked,
            tooltip="Configure swap settings",
        )
        button_box.append(settings_btn)

        # Apply button
        apply_btn = create_action_button(
            "Apply",
            icon_name="emblem-ok-symbolic",
            style="suggested-action",
            on_clicked=self._on_apply_clicked,
            tooltip="Apply configuration changes",
        )
        button_box.append(apply_btn)

        main_box.append(button_box)

        clamp.set_child(main_box)
        scrolled.set_child(clamp)
        self.set_child(scrolled)

    def _start_monitoring(self) -> None:
        """Start periodic status updates."""
        # Start memory monitoring
        self._meminfo_service.start_monitoring(
            self._on_memory_update,
            CHART_UPDATE_INTERVAL_MS,
        )

        # Update swap status periodically (less frequently)
        self._status_timer = GLib.timeout_add(5000, self._update_swap_status)

        # Initial status update
        self._update_swap_status()

    def stop_monitoring(self) -> None:
        """Stop periodic updates (called when view is destroyed)."""
        self._meminfo_service.stop_monitoring()
        if self._status_timer:
            GLib.source_remove(self._status_timer)
            self._status_timer = 0

    def _on_memory_update(self, stats: MemoryStats) -> None:
        """
        Handle memory stats update.

        Args:
            stats: Current memory statistics
        """
        # Update chart
        if self._chart:
            mem_text = f"{stats.mem_used_formatted} / {stats.mem_total_formatted}"
            swap_text = (
                f"{stats.swap_used_formatted} / {stats.swap_total_formatted}"
                if stats.swap_total > 0
                else "N/A"
            )

            self._chart.add_data_point(
                stats.mem_used_percent,
                stats.swap_used_percent,
                mem_text,
                swap_text,
            )

        # Update bars
        if self._bars:
            mem_text = f"{stats.mem_used_formatted} / {stats.mem_total_formatted}"
            swap_text = (
                f"{stats.swap_used_formatted} / {stats.swap_total_formatted}"
                if stats.swap_total > 0
                else "No swap"
            )
            self._bars.update(
                stats.mem_used_percent,
                mem_text,
                stats.swap_used_percent,
                swap_text,
            )

    def _update_swap_status(self) -> bool:
        """
        Update swap service status display.

        Returns:
            bool: True to continue timer
        """
        status = self._swap_service.get_status()

        # Update service state
        state_text = status.service_state.value.capitalize()
        is_active = status.service_state == ServiceState.ACTIVE

        update_status_row(self._status_row, state_text)

        # Update indicator
        if self._status_indicator:
            # Remove old indicator
            self._status_row.remove(self._status_indicator)
            # Create new indicator
            self._status_indicator = create_status_indicator(is_active, "")
            self._status_row.add_suffix(self._status_indicator)

        # Update mode
        config = self._config_service.get()
        mode_text = config.mode.value
        if self._mode_row:
            update_status_row(self._mode_row, mode_text)

        # Update Zswap stats
        if status.zswap.enabled:
            self._zswap_group.set_visible(True)
            update_status_row(
                self._zswap_compressor_row, status.zswap.compressor or "-"
            )

            if status.zswap.pool_size_bytes > 0:
                pool_text = self._format_bytes(status.zswap.pool_size_bytes)
                update_status_row(self._zswap_pool_row, pool_text)
            else:
                update_status_row(self._zswap_pool_row, "-")

            if status.zswap.stored_data_bytes > 0:
                stored_text = self._format_bytes(status.zswap.stored_data_bytes)
                update_status_row(self._zswap_stored_row, stored_text)
            else:
                update_status_row(self._zswap_stored_row, "-")

            if status.zswap.compress_ratio > 0:
                ratio_text = f"{status.zswap.compress_ratio:.1f}x"
                update_status_row(self._zswap_ratio_row, ratio_text)
            else:
                update_status_row(self._zswap_ratio_row, "-")
        else:
            self._zswap_group.set_visible(False)

        # Update Zram stats
        if status.zram.enabled:
            self._zram_group.set_visible(True)
            if status.zram.total_size_bytes > 0:
                size_text = self._format_bytes(status.zram.total_size_bytes)
                update_status_row(self._zram_size_row, size_text)
            else:
                update_status_row(self._zram_size_row, "-")
        else:
            self._zram_group.set_visible(False)

        # Update SwapFile stats
        if status.swapfile.enabled:
            self._swapfile_group.set_visible(True)
            files_text = f"{status.swapfile.file_count} / {status.swapfile.max_files}"
            update_status_row(self._swapfile_files_row, files_text)

            if status.swapfile.total_size_bytes > 0:
                size_text = self._format_bytes(status.swapfile.total_size_bytes)
                update_status_row(self._swapfile_size_row, size_text)
            else:
                update_status_row(self._swapfile_size_row, "-")
        else:
            self._swapfile_group.set_visible(False)

        return True  # Continue timer

    def _format_bytes(self, size_bytes: int) -> str:
        """Format bytes to human-readable string."""
        units = ["B", "KiB", "MiB", "GiB", "TiB"]
        unit_index = 0
        size = float(size_bytes)

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        return f"{size:.1f} {units[unit_index]}"

    def _on_settings_clicked(self) -> None:
        """Handle settings button click."""
        if self._on_navigate_settings:
            self._on_navigate_settings()

    def _on_apply_clicked(self) -> None:
        """Handle apply button click."""
        if self._on_apply:
            self._on_apply()

    def refresh(self) -> None:
        """Refresh all data from system."""
        self._config_service.reload()
        self._update_swap_status()

    def _show_toast(self, message: str, timeout: int = 3) -> None:
        """Show a toast notification."""
        if self._on_toast:
            self._on_toast(message, timeout)
