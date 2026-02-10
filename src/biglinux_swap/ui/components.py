#!/usr/bin/env python3
"""
Reusable UI components for BigLinux Swap Manager.

Factory functions for creating consistent Adwaita widgets.
"""

from __future__ import annotations

from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk


def create_preferences_group(
    title: str,
    description: str | None = None,
) -> Adw.PreferencesGroup:
    """Create a preferences group with title and optional description."""
    group = Adw.PreferencesGroup()
    group.set_title(title)
    if description:
        group.set_description(description)
    return group


def create_action_row_with_switch(
    title: str,
    subtitle: str | None = None,
    active: bool = False,
    on_toggled: Callable[[bool], None] | None = None,
) -> tuple[Adw.ActionRow, Gtk.Switch]:
    """Create an action row with a switch."""
    row = Adw.ActionRow()
    row.set_title(title)
    if subtitle:
        row.set_subtitle(subtitle)

    switch = Gtk.Switch()
    switch.set_active(active)
    switch.set_valign(Gtk.Align.CENTER)

    if on_toggled:
        switch.connect("notify::active", lambda s, _: on_toggled(s.get_active()))

    row.add_suffix(switch)
    row.set_activatable_widget(switch)
    return row, switch


def create_action_row_with_scale(
    title: str,
    subtitle: str | None = None,
    min_value: float = 0.0,
    max_value: float = 100.0,
    value: float = 50.0,
    step: float = 1.0,
    digits: int = 0,
    on_changed: Callable[[float], None] | None = None,
    show_value: bool = True,
) -> tuple[Adw.ActionRow, Gtk.Scale]:
    """Create an action row with a horizontal scale slider."""
    row = Adw.ActionRow()
    row.set_title(title)
    if subtitle:
        row.set_subtitle(subtitle)

    adjustment = Gtk.Adjustment(
        value=value,
        lower=min_value,
        upper=max_value,
        step_increment=step,
        page_increment=step * 10,
    )

    scale = Gtk.Scale(
        orientation=Gtk.Orientation.HORIZONTAL,
        adjustment=adjustment,
    )
    scale.set_digits(digits)
    scale.set_hexpand(True)
    scale.set_size_request(200, -1)
    scale.set_valign(Gtk.Align.CENTER)
    scale.set_draw_value(show_value)

    if on_changed:
        scale.connect("value-changed", lambda s: on_changed(s.get_value()))

    row.add_suffix(scale)
    return row, scale


def create_combo_row(
    title: str,
    subtitle: str | None = None,
    options: list[str] | None = None,
    selected_index: int = 0,
    on_selected: Callable[[int], None] | None = None,
) -> Adw.ComboRow:
    """Create a combo row with dropdown options."""
    row = Adw.ComboRow()
    row.set_title(title)
    if subtitle:
        row.set_subtitle(subtitle)

    if options:
        model = Gtk.StringList.new(options)
        row.set_model(model)
        row.set_selected(selected_index)

    if on_selected:
        row.connect("notify::selected", lambda r, _: on_selected(r.get_selected()))

    return row


def create_status_row(
    label: str,
    value: str,
) -> Adw.ActionRow:
    """Create a status display row (read-only)."""
    row = Adw.ActionRow()
    row.set_title(label)
    row.set_activatable(False)

    value_label = Gtk.Label(label=value)
    value_label.add_css_class("dim-label")
    value_label.set_valign(Gtk.Align.CENTER)
    row.add_suffix(value_label)

    row._value_label = value_label  # type: ignore[attr-defined]
    return row


def update_status_row(row: Adw.ActionRow | None, value: str) -> None:
    """Update the value displayed in a status row."""
    if row and hasattr(row, "_value_label"):
        row._value_label.set_text(value)  # type: ignore[attr-defined]


def create_status_indicator(
    active: bool = False,
    label: str | None = None,
) -> Gtk.Box:
    """Create a status indicator with colored dot."""
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    box.set_valign(Gtk.Align.CENTER)

    dot = Gtk.Label(label="●")
    if active:
        dot.add_css_class("success")
    else:
        dot.add_css_class("dim-label")
    box.append(dot)

    if label:
        lbl = Gtk.Label(label=label)
        lbl.add_css_class("dim-label")
        box.append(lbl)

    return box
