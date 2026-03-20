"""
macOS-specific window helpers.
Makes windows stay visible during Mission Control (F3),
Spaces transitions, and full-screen apps.
"""
import sys
import ctypes


def pin_window_above_mission_control(qt_widget):
    """
    Use Cocoa APIs to make *qt_widget* stick above Mission Control.
    No-op on non-macOS platforms.
    """
    if sys.platform != "darwin":
        return

    try:
        from Cocoa import (
            NSApplication,
            NSWindowCollectionBehaviorCanJoinAllSpaces,
            NSWindowCollectionBehaviorStationary,
            NSWindowCollectionBehaviorFullScreenAuxiliary,
            NSWindowCollectionBehaviorIgnoresCycle,
        )
        import objc
    except ImportError:
        return

    # Force the widget to have a native window handle
    qt_widget.winId()

    # Get all NSWindows and find the one matching our widget's geometry
    app = NSApplication.sharedApplication()

    # Use objc runtime to get NSView from the Qt winId
    view_ptr = int(qt_widget.winId())
    ns_view = objc.objc_object(c_void_p=ctypes.c_void_p(view_ptr))
    ns_window = ns_view.window()

    if ns_window is None:
        return

    # kCGStatusWindowLevel = 25 — above Mission Control
    ns_window.setLevel_(25)

    behavior = (
        NSWindowCollectionBehaviorCanJoinAllSpaces
        | NSWindowCollectionBehaviorStationary
        | NSWindowCollectionBehaviorFullScreenAuxiliary
        | NSWindowCollectionBehaviorIgnoresCycle
    )
    ns_window.setCollectionBehavior_(behavior)
