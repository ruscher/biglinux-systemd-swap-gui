#!/usr/bin/env python3
"""
Memory chart widget using Cairo drawing.

Displays real-time memory and swap usage in a line chart.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from biglinux_swap.config import CHART_MAX_HISTORY

# Import cairo for type hints
try:
    import cairo
except ImportError:
    cairo = None  # type: ignore[assignment]


@dataclass
class MemoryDataPoint:
    """Single data point for memory chart."""

    mem_used_percent: float
    swap_used_percent: float
    zswap_percent: float = 0.0  # Zswap as percentage of total RAM
    # Absolute values for tooltip
    mem_text: str = ""
    swap_text: str = ""
    zswap_text: str = ""


class MemoryChartWidget(Gtk.DrawingArea):
    """
    Custom widget to display memory and swap usage over time.

    Shows a line chart with:
    - Green line: RAM usage percentage
    - Blue line: Swap usage percentage
    - Grid background with percentage labels
    - Hover tooltip showing values at mouse position
    """

    def __init__(self) -> None:
        """Initialize the memory chart widget."""
        super().__init__()

        self._history: deque[MemoryDataPoint] = deque(maxlen=CHART_MAX_HISTORY)

        # Current values for display
        self._mem_used_text = ""
        self._swap_used_text = ""
        self._zswap_text = ""

        # Hover state
        self._hover_x: float | None = None
        self._hover_index: int | None = None

        # Sizing
        self.set_size_request(300, 150)
        self.set_vexpand(False)
        self.set_hexpand(True)

        # Connect draw signal
        self.set_draw_func(self._on_draw)

        # Mouse tracking for hover
        motion_controller = Gtk.EventControllerMotion()
        motion_controller.connect("motion", self._on_motion)
        motion_controller.connect("leave", self._on_leave)
        self.add_controller(motion_controller)

    def add_data_point(
        self,
        mem_used_percent: float,
        swap_used_percent: float,
        mem_used_text: str = "",
        swap_used_text: str = "",
        zswap_percent: float = 0.0,
        zswap_text: str = "",
    ) -> None:
        """
        Add a new data point and trigger redraw.

        Args:
            mem_used_percent: RAM usage percentage (0-100)
            swap_used_percent: Swap usage percentage (0-100)
            mem_used_text: Formatted text for RAM usage
            swap_used_text: Formatted text for swap usage
            zswap_percent: Zswap pool as percentage of RAM (0-100)
            zswap_text: Formatted text for zswap pool size
        """
        point = MemoryDataPoint(
            mem_used_percent=min(100.0, max(0.0, mem_used_percent)),
            swap_used_percent=min(100.0, max(0.0, swap_used_percent)),
            zswap_percent=min(100.0, max(0.0, zswap_percent)),
            mem_text=mem_used_text,
            swap_text=swap_used_text,
            zswap_text=zswap_text,
        )
        self._history.append(point)
        self._mem_used_text = mem_used_text
        self._swap_used_text = swap_used_text
        self._zswap_text = zswap_text
        self.queue_draw()

    def clear(self) -> None:
        """Clear all data points."""
        self._history.clear()
        self._mem_used_text = ""
        self._swap_used_text = ""
        self._zswap_text = ""
        self.queue_draw()

    def _on_motion(
        self,
        controller: Gtk.EventControllerMotion,
        x: float,
        y: float,
    ) -> None:
        """Handle mouse motion for hover tooltip."""
        self._hover_x = x
        self._update_hover_index()
        self.queue_draw()

    def _on_leave(self, controller: Gtk.EventControllerMotion) -> None:
        """Handle mouse leaving the widget."""
        self._hover_x = None
        self._hover_index = None
        self.queue_draw()

    def _update_hover_index(self) -> None:
        """Calculate which data point the mouse is hovering over."""
        if self._hover_x is None or not self._history:
            self._hover_index = None
            return

        # Get widget dimensions
        width = self.get_width()
        margin_left = 45
        margin_right = 10
        chart_width = width - margin_left - margin_right

        if chart_width <= 0:
            self._hover_index = None
            return

        # Check if mouse is within chart area
        if self._hover_x < margin_left or self._hover_x > width - margin_right:
            self._hover_index = None
            return

        # Calculate which point the mouse is near
        num_points = len(self._history)
        x_step = chart_width / max(CHART_MAX_HISTORY - 1, 1)
        start_x = margin_left + chart_width - (num_points - 1) * x_step

        # Find closest point
        relative_x = self._hover_x - start_x
        index = round(relative_x / x_step) if x_step > 0 else 0
        index = max(0, min(num_points - 1, index))
        self._hover_index = index

    def _on_draw(
        self,
        area: Gtk.DrawingArea,
        cr: cairo.Context,
        width: int,
        height: int,
    ) -> None:
        """Draw the chart using Cairo."""
        # Background
        cr.set_source_rgba(0.1, 0.1, 0.1, 0.9)
        cr.rectangle(0, 0, width, height)
        cr.fill()

        # Margins
        margin_left = 45
        margin_right = 10
        margin_top = 15
        margin_bottom = 30

        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom

        if chart_width <= 0 or chart_height <= 0:
            return

        # Draw grid lines
        cr.set_source_rgba(0.3, 0.3, 0.3, 0.5)
        cr.set_line_width(1)

        for percent in [25, 50, 75, 100]:
            y = margin_top + chart_height * (1 - percent / 100)
            cr.move_to(margin_left, y)
            cr.line_to(margin_left + chart_width, y)
            cr.stroke()

            # Label
            cr.set_source_rgba(0.6, 0.6, 0.6, 1)
            cr.select_font_face("Sans", 0, 0)
            cr.set_font_size(10)
            cr.move_to(5, y + 4)
            cr.show_text(f"{percent}%")

        # Draw 0% line
        y_zero = margin_top + chart_height
        cr.set_source_rgba(0.3, 0.3, 0.3, 0.5)
        cr.move_to(margin_left, y_zero)
        cr.line_to(margin_left + chart_width, y_zero)
        cr.stroke()

        cr.set_source_rgba(0.6, 0.6, 0.6, 1)
        cr.move_to(5, y_zero + 4)
        cr.show_text("0%")

        if not self._history:
            # No data - show placeholder text
            cr.set_source_rgba(0.5, 0.5, 0.5, 1)
            cr.set_font_size(14)
            text = "Collecting data..."
            extents = cr.text_extents(text)
            cr.move_to(
                margin_left + (chart_width - extents.width) / 2,
                margin_top + chart_height / 2,
            )
            cr.show_text(text)
            return

        # Check if we have swap data (not just zswap, but any swap configuration)
        # If the last point has swap text other than empty/"N/A", we show 3-line layout
        last_point = list(self._history)[-1] if self._history else None
        has_swap = last_point and last_point.swap_text and last_point.swap_text != "N/A"

        # Draw RAM line (green)
        self._draw_line(
            cr,
            chart_width,
            chart_height,
            margin_left,
            margin_top,
            [p.mem_used_percent for p in self._history],
            (0.3, 0.85, 0.4, 1.0),  # Green
        )

        # Draw Swap in RAM line (orange) - always draw when swap exists
        if has_swap:
            self._draw_line(
                cr,
                chart_width,
                chart_height,
                margin_left,
                margin_top,
                [p.zswap_percent for p in self._history],
                (0.95, 0.6, 0.2, 1.0),  # Orange
            )

        # Draw Swap line (blue)
        self._draw_line(
            cr,
            chart_width,
            chart_height,
            margin_left,
            margin_top,
            [p.swap_used_percent for p in self._history],
            (0.3, 0.5, 0.95, 1.0),  # Blue
        )

        # Legend at bottom - adjust spacing based on whether we have swap
        legend_y = height - 12

        if has_swap:
            # Three-item legend: RAM, Swap in RAM (zswap), Swap on Disk
            legend_spacing = chart_width / 3

            # RAM legend
            cr.set_source_rgba(0.3, 0.85, 0.4, 1.0)
            cr.rectangle(margin_left + 5, legend_y - 8, 12, 8)
            cr.fill()
            cr.set_source_rgba(0.9, 0.9, 0.9, 1)
            cr.set_font_size(10)
            cr.move_to(margin_left + 22, legend_y)
            ram_text = f"RAM: {self._mem_used_text}" if self._mem_used_text else "RAM"
            cr.show_text(ram_text)

            # Swap in RAM legend (zswap stored data)
            zswap_x = margin_left + legend_spacing
            cr.set_source_rgba(0.95, 0.6, 0.2, 1.0)
            cr.rectangle(zswap_x, legend_y - 8, 12, 8)
            cr.fill()
            cr.set_source_rgba(0.9, 0.9, 0.9, 1)
            cr.move_to(zswap_x + 17, legend_y)
            zswap_legend = (
                f"Swap RAM: {self._zswap_text}" if self._zswap_text else "Swap RAM"
            )
            cr.show_text(zswap_legend)

            # Swap on Disk legend
            swap_x = margin_left + 2 * legend_spacing
            cr.set_source_rgba(0.3, 0.5, 0.95, 1.0)
            cr.rectangle(swap_x, legend_y - 8, 12, 8)
            cr.fill()
            cr.set_source_rgba(0.9, 0.9, 0.9, 1)
            cr.move_to(swap_x + 17, legend_y)
            swap_text = (
                f"Swap Disk: {self._swap_used_text}"
                if self._swap_used_text
                else "Swap Disk"
            )
            cr.show_text(swap_text)
        else:
            # Two-item legend: RAM, Swap
            # RAM legend
            cr.set_source_rgba(0.3, 0.85, 0.4, 1.0)
            cr.rectangle(margin_left + 5, legend_y - 8, 12, 8)
            cr.fill()
            cr.set_source_rgba(0.9, 0.9, 0.9, 1)
            cr.set_font_size(11)
            cr.move_to(margin_left + 22, legend_y)
            ram_text = f"RAM: {self._mem_used_text}" if self._mem_used_text else "RAM"
            cr.show_text(ram_text)

            # Swap legend
            swap_x = margin_left + chart_width / 2
            cr.set_source_rgba(0.3, 0.5, 0.95, 1.0)
            cr.rectangle(swap_x, legend_y - 8, 12, 8)
            cr.fill()
            cr.set_source_rgba(0.9, 0.9, 0.9, 1)
            cr.move_to(swap_x + 17, legend_y)
            swap_text = (
                f"Swap: {self._swap_used_text}" if self._swap_used_text else "Swap"
            )
            cr.show_text(swap_text)

        # Draw hover indicator and tooltip
        if self._hover_index is not None and 0 <= self._hover_index < len(
            self._history
        ):
            point = list(self._history)[self._hover_index]
            num_points = len(self._history)
            x_step = chart_width / max(CHART_MAX_HISTORY - 1, 1)
            start_x = margin_left + chart_width - (num_points - 1) * x_step
            hover_x = start_x + self._hover_index * x_step

            # Vertical line
            cr.set_source_rgba(1, 1, 1, 0.3)
            cr.set_line_width(1)
            cr.move_to(hover_x, margin_top)
            cr.line_to(hover_x, margin_top + chart_height)
            cr.stroke()

            # RAM point
            ram_y = margin_top + chart_height * (1 - point.mem_used_percent / 100)
            cr.set_source_rgba(0.3, 0.85, 0.4, 1.0)
            cr.arc(hover_x, ram_y, 4, 0, 2 * 3.14159)
            cr.fill()

            # Zswap point (if data exists)
            if point.zswap_percent > 0:
                zswap_y = margin_top + chart_height * (1 - point.zswap_percent / 100)
                cr.set_source_rgba(0.95, 0.6, 0.2, 1.0)
                cr.arc(hover_x, zswap_y, 4, 0, 2 * 3.14159)
                cr.fill()

            # Swap point
            swap_y = margin_top + chart_height * (1 - point.swap_used_percent / 100)
            cr.set_source_rgba(0.3, 0.5, 0.95, 1.0)
            cr.arc(hover_x, swap_y, 4, 0, 2 * 3.14159)
            cr.fill()

            # Calculate how many seconds ago this reading was
            seconds_ago = num_points - self._hover_index - 1

            # Build tooltip text with absolute values and time
            time_text = f"{seconds_ago}s ago" if seconds_ago > 0 else "now"
            # Always show Swap RAM and Swap Disk when swap is configured
            has_swap_text = point.swap_text and point.swap_text != "N/A"
            if has_swap_text:
                zswap_display = point.zswap_text if point.zswap_text else "0 B"
                tooltip_text = f"[{time_text}]  RAM: {point.mem_text}  Swap RAM: {zswap_display}  Swap Disk: {point.swap_text}"
            elif point.mem_text:
                tooltip_text = f"[{time_text}]  RAM: {point.mem_text}"
            else:
                # Fallback to percentages if no text available
                tooltip_text = f"[{time_text}]  RAM: {point.mem_used_percent:.1f}%"
            cr.set_font_size(10)
            extents = cr.text_extents(tooltip_text)

            # Fixed position: top-right corner
            tooltip_x = width - margin_right - extents.width - 10
            tooltip_y = margin_top + 5

            # Background
            cr.set_source_rgba(0.15, 0.15, 0.15, 0.95)
            cr.rectangle(
                tooltip_x - 5, tooltip_y - 3, extents.width + 10, extents.height + 8
            )
            cr.fill()

            # Border
            cr.set_source_rgba(0.4, 0.4, 0.4, 1)
            cr.set_line_width(1)
            cr.rectangle(
                tooltip_x - 5, tooltip_y - 3, extents.width + 10, extents.height + 8
            )
            cr.stroke()

            # Text
            cr.set_source_rgba(0.95, 0.95, 0.95, 1)
            cr.move_to(tooltip_x, tooltip_y + extents.height)
            cr.show_text(tooltip_text)

    def _draw_line(
        self,
        cr: cairo.Context,
        chart_width: float,
        chart_height: float,
        margin_left: float,
        margin_top: float,
        values: list[float],
        color: tuple[float, float, float, float],
    ) -> None:
        """
        Draw a line on the chart.

        Args:
            cr: Cairo context
            chart_width: Width of chart area
            chart_height: Height of chart area
            margin_left: Left margin
            margin_top: Top margin
            values: List of values (0-100)
            color: RGBA color tuple
        """
        if not values:
            return

        cr.set_source_rgba(*color)
        cr.set_line_width(2)

        num_points = len(values)
        x_step = chart_width / max(CHART_MAX_HISTORY - 1, 1)

        # Start from the right side
        start_x = margin_left + chart_width - (num_points - 1) * x_step

        for i, value in enumerate(values):
            x = start_x + i * x_step
            y = margin_top + chart_height * (1 - value / 100)

            if i == 0:
                cr.move_to(x, y)
            else:
                cr.line_to(x, y)

        cr.stroke()

        # Draw area fill with transparency
        cr.set_source_rgba(color[0], color[1], color[2], 0.15)

        # Start again for fill
        for i, value in enumerate(values):
            x = start_x + i * x_step
            y = margin_top + chart_height * (1 - value / 100)

            if i == 0:
                cr.move_to(x, y)
            else:
                cr.line_to(x, y)

        # Close path to bottom
        cr.line_to(start_x + (num_points - 1) * x_step, margin_top + chart_height)
        cr.line_to(start_x, margin_top + chart_height)
        cr.close_path()
        cr.fill()


class MemoryBarsWidget(Gtk.Box):
    """
    Widget showing memory and swap usage as horizontal bars with labels.

    Alternative to the chart for simpler display.
    """

    def __init__(self) -> None:
        """Initialize the memory bars widget."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_margin_top(12)
        self.set_margin_bottom(12)

        # RAM bar
        ram_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        ram_label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        ram_title = Gtk.Label(label="RAM")
        ram_title.set_halign(Gtk.Align.START)
        ram_title.add_css_class("heading")
        ram_label_box.append(ram_title)

        self._ram_value_label = Gtk.Label(label="")
        self._ram_value_label.set_halign(Gtk.Align.END)
        self._ram_value_label.set_hexpand(True)
        self._ram_value_label.add_css_class("dim-label")
        ram_label_box.append(self._ram_value_label)

        ram_box.append(ram_label_box)

        self._ram_bar = Gtk.LevelBar()
        self._ram_bar.set_min_value(0)
        self._ram_bar.set_max_value(100)
        self._ram_bar.set_value(0)
        self._ram_bar.add_offset_value("low", 50)
        self._ram_bar.add_offset_value("high", 75)
        self._ram_bar.add_offset_value("full", 90)
        ram_box.append(self._ram_bar)

        self.append(ram_box)

        # Swap bar
        swap_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        swap_label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        swap_title = Gtk.Label(label="Swap")
        swap_title.set_halign(Gtk.Align.START)
        swap_title.add_css_class("heading")
        swap_label_box.append(swap_title)

        self._swap_value_label = Gtk.Label(label="")
        self._swap_value_label.set_halign(Gtk.Align.END)
        self._swap_value_label.set_hexpand(True)
        self._swap_value_label.add_css_class("dim-label")
        swap_label_box.append(self._swap_value_label)

        swap_box.append(swap_label_box)

        self._swap_bar = Gtk.LevelBar()
        self._swap_bar.set_min_value(0)
        self._swap_bar.set_max_value(100)
        self._swap_bar.set_value(0)
        self._swap_bar.add_offset_value("low", 30)
        self._swap_bar.add_offset_value("high", 60)
        self._swap_bar.add_offset_value("full", 90)
        swap_box.append(self._swap_bar)

        self.append(swap_box)

    def update(
        self,
        mem_percent: float,
        mem_text: str,
        swap_percent: float,
        swap_text: str,
    ) -> None:
        """
        Update the bars with new values.

        Args:
            mem_percent: RAM usage percentage
            mem_text: RAM usage text (e.g., "8.2 / 16 GiB")
            swap_percent: Swap usage percentage
            swap_text: Swap usage text
        """
        self._ram_bar.set_value(mem_percent)
        self._ram_value_label.set_text(mem_text)

        self._swap_bar.set_value(swap_percent)
        self._swap_value_label.set_text(swap_text)
