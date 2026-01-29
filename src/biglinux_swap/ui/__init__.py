"""UI modules for BigLinux Swap Manager."""

from biglinux_swap.ui.base_view import BaseView, ScrollableView
from biglinux_swap.ui.main_view import MainView
from biglinux_swap.ui.memory_chart import MemoryBarsWidget, MemoryChartWidget
from biglinux_swap.ui.settings_view import SettingsView
from biglinux_swap.ui.unified_view import UnifiedView

__all__ = [
    "BaseView",
    "MainView",
    "MemoryBarsWidget",
    "MemoryChartWidget",
    "ScrollableView",
    "SettingsView",
    "UnifiedView",
]
