"""macOS-specific window helpers.

Makes windows stay visible during Mission Control (F3), Spaces
transitions, and full-screen apps by setting Cocoa window level and
collection-behavior flags.
"""

from __future__ import annotations

import ctypes
import sys

# kCGStatusWindowLevel — renders above Mission Control.
_STATUS_WINDOW_LEVEL = 25


def pin_window_above_mission_control(qt_widget: object) -> None:
    """Pin *qt_widget* above Mission Control using Cocoa APIs.

    Sets the underlying ``NSWindow`` level to ``kCGStatusWindowLevel``
    and applies collection-behavior flags so the window persists across
    Spaces and full-screen transitions.

    No-op on non-macOS platforms or when ``pyobjc`` is unavailable.

    Args:
        qt_widget: Any ``QWidget`` instance.
    """
    if sys.platform != "darwin":
        return

    try:
        from Cocoa import (  # type: ignore[import-untyped]
            NSWindowCollectionBehaviorCanJoinAllSpaces,
            NSWindowCollectionBehaviorStationary,
            NSWindowCollectionBehaviorFullScreenAuxiliary,
            NSWindowCollectionBehaviorIgnoresCycle,
        )
        import objc  # type: ignore[import-untyped]
    except ImportError:
        return

    # Force native window handle creation.
    qt_widget.winId()  # type: ignore[attr-defined]

    view_ptr = int(qt_widget.winId())  # type: ignore[attr-defined]
    ns_view = objc.objc_object(c_void_p=ctypes.c_void_p(view_ptr))
    ns_window = ns_view.window()

    if ns_window is None:
        return

    ns_window.setLevel_(_STATUS_WINDOW_LEVEL)

    behavior = (
        NSWindowCollectionBehaviorCanJoinAllSpaces
        | NSWindowCollectionBehaviorStationary
        | NSWindowCollectionBehaviorFullScreenAuxiliary
        | NSWindowCollectionBehaviorIgnoresCycle
    )
    ns_window.setCollectionBehavior_(behavior)
