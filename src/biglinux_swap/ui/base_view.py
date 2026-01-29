#!/usr/bin/env python3
"""
Base view classes for BigLinux Swap Manager UI.

Provides base classes and common functionality for all views.
Note: We cannot use ABC with GObject-based classes due to metaclass conflicts.
Instead, we use NotImplementedError for abstract method enforcement.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk

if TYPE_CHECKING:
    from biglinux_swap.services import ConfigService, MeminfoService, SwapService

logger = logging.getLogger(__name__)


class BaseView(Adw.NavigationPage):
    """
    Base class for all application views.

    Provides common functionality:
    - Service injection
    - Navigation support
    - Loading state handling

    Note: Subclasses MUST override _setup_ui() and _load_state().
    """

    __gtype_name__ = "BaseView"

    def __init__(
        self,
        title: str,
        tag: str,
        config_service: ConfigService,
        swap_service: SwapService,
        meminfo_service: MeminfoService,
        on_toast: Callable[[str, int], None] | None = None,
    ) -> None:
        """
        Initialize the base view.

        Args:
            title: View title for navigation
            tag: Unique tag for navigation
            config_service: Configuration service
            swap_service: Swap status service
            meminfo_service: Memory info service
            on_toast: Callback to show toast notifications
        """
        super().__init__(title=title, tag=tag)

        self._config_service = config_service
        self._swap_service = swap_service
        self._meminfo_service = meminfo_service
        self._on_toast = on_toast
        self._is_loading = False

        # Setup UI
        self._setup_ui()
        self._load_state()

    def _setup_ui(self) -> None:
        """Set up the view's UI layout. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement _setup_ui()")

    def _load_state(self) -> None:
        """Load current state. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement _load_state()")

    def _navigate_to(self, tag: str) -> None:
        """
        Navigate to another view.

        Args:
            tag: Target view tag
        """
        nav_view = self.get_ancestor(Adw.NavigationView)
        if nav_view:
            nav_view.push_by_tag(tag)

    def _set_loading(self, loading: bool) -> None:
        """
        Set loading state for the view.

        Args:
            loading: True if loading, False otherwise
        """
        self._is_loading = loading
        self.set_sensitive(not loading)

    def _show_toast(self, message: str, timeout: int = 3) -> None:
        """
        Show a toast notification.

        Args:
            message: Toast message
            timeout: Duration in seconds
        """
        if self._on_toast:
            self._on_toast(message, timeout)

    def _schedule_update(
        self, callback: Callable[[], bool], delay_ms: int = 100
    ) -> int:
        """
        Schedule a delayed update.

        Args:
            callback: Function to call
            delay_ms: Delay in milliseconds

        Returns:
            int: Timer ID (can be used to cancel)
        """
        return GLib.timeout_add(delay_ms, callback)


class ScrollableView(BaseView):
    """
    Base view with scrollable content area.

    Provides:
    - Scrolled window container
    - Content clamp for responsive layout
    - Main box for content

    Note: Subclasses must override _build_content() and _load_state().
    """

    __gtype_name__ = "ScrollableView"

    def __init__(
        self,
        title: str,
        tag: str,
        config_service: ConfigService,
        swap_service: SwapService,
        meminfo_service: MeminfoService,
        on_toast: Callable[[str, int], None] | None = None,
        max_content_width: int = 600,
    ) -> None:
        """
        Initialize the scrollable view.

        Args:
            title: View title
            tag: View tag
            config_service: Configuration service
            swap_service: Swap status service
            meminfo_service: Memory info service
            on_toast: Toast callback
            max_content_width: Maximum content width in pixels
        """
        self._max_content_width = max_content_width
        self._content_box: Gtk.Box | None = None
        super().__init__(
            title, tag, config_service, swap_service, meminfo_service, on_toast
        )

    def _setup_ui(self) -> None:
        """Set up scrollable content area."""
        # Scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)

        # Clamp for content width
        clamp = Adw.Clamp()
        clamp.set_maximum_size(self._max_content_width)
        clamp.set_margin_top(12)
        clamp.set_margin_bottom(24)
        clamp.set_margin_start(12)
        clamp.set_margin_end(12)

        # Main content box
        self._content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)

        # Build view-specific content
        self._build_content()

        clamp.set_child(self._content_box)
        scrolled.set_child(clamp)
        self.set_child(scrolled)

    def _build_content(self) -> None:
        """Build view-specific content in self._content_box. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement _build_content()")

    def _add_group(self, group: Adw.PreferencesGroup) -> None:
        """
        Add a preferences group to the content.

        Args:
            group: PreferencesGroup to add
        """
        if self._content_box is not None:
            self._content_box.append(group)

    def _add_widget(self, widget: Gtk.Widget) -> None:
        """
        Add a widget to the content.

        Args:
            widget: Widget to add
        """
        if self._content_box is not None:
            self._content_box.append(widget)
