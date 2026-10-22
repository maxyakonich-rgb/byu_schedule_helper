import collections
import sys
import tkinter as tk
import customtkinter as ctk

# Pixel-level sensitivity tuning (with yscrollincrement=1, 1 unit = 1 pixel)
MAC_TRACKPAD_PIXEL_SCALE = 1.0
MAC_WHEEL_LINE_PIXELS = 28.0
WIN_WHEEL_STEP_PIXELS = 36

_ACTIVE_CANVASES = {}
_COCOA_MONITOR = None
_SCROLL_QUEUE = collections.deque()
_POLL_SCHEDULED = False

IS_MAC = sys.platform == "darwin"
IS_WINDOWS = sys.platform.startswith("win")

HAS_COCOA = False
if IS_MAC:
    try:
        from AppKit import NSApp, NSEvent, NSEventMaskScrollWheel
        HAS_COCOA = True
    except ImportError:
        HAS_COCOA = False


def _cocoa_scroll_handler(event):
    """Pure Cocoa event reader.

    Performs NO Tkinter/Python GUI queries here to completely prevent
    Python 3.14 GIL / PyEval_RestoreThread crashes.
    """
    if not _ACTIVE_CANVASES:
        return event

    try:
        raw_dy = event.scrollingDeltaY()
        if raw_dy == 0:
            return event

        # Distinguish pixel-precise trackpad deltas from notched mouse wheels
        try:
            is_precise = bool(event.hasPreciseScrollingDeltas())
        except Exception:
            is_precise = True

        if is_precise:
            dy_px = float(raw_dy) * MAC_TRACKPAD_PIXEL_SCALE
        else:
            dy_px = float(raw_dy) * MAC_WHEEL_LINE_PIXELS

        # Get screen coordinates directly from Cocoa event, not from Tkinter
        loc = event.locationInWindow()
        win = event.window()
        if win is not None:
            screen_loc = win.convertPointToScreen_(loc)
            screen_x = screen_loc.x
            # Cocoa origin is bottom-left; convert to top-left screen coordinates
            screen_h = win.screen().frame().size.height if win.screen() else 1000
            screen_y = screen_h - screen_loc.y
        else:
            screen_x, screen_y = None, None

        # Queue the pixel delta for coalesced consumption on Tkinter's main thread
        _SCROLL_QUEUE.append((dy_px, screen_x, screen_y))
        # Consume the native event so Tk/CustomTkinter does not double-scroll with giant jumps
        return None
    except Exception:
        return event


def _start_cocoa_monitor():
    global _COCOA_MONITOR
    if HAS_COCOA and _COCOA_MONITOR is None:
        try:
            _COCOA_MONITOR = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
                NSEventMaskScrollWheel, _cocoa_scroll_handler
            )
        except Exception:
            pass


def _poll_scroll_queue(root):
    """Executes on Tkinter's main loop with the GIL held.
    Coalesces all queued trackpad/wheel events into a single pixel scroll per frame,
    routing to the topmost window/modal canvas under the pointer.
    """
    global _POLL_SCHEDULED
    if not root or not root.winfo_exists():
        _POLL_SCHEDULED = False
        return

    try:
        if _SCROLL_QUEUE:
            total_dy_px = 0.0

            # Coalesce all events accumulated during this frame into one smooth delta
            while _SCROLL_QUEUE:
                dy_px, _, _ = _SCROLL_QUEUE.popleft()
                total_dy_px += dy_px

            ptr_x = root.winfo_pointerx()
            ptr_y = root.winfo_pointery()

            target_canvas = None

            # 1. Check the exact topmost widget under the cursor (respects Toplevel modals like ReviewsModal)
            try:
                hovered = root.winfo_containing(ptr_x, ptr_y)
                curr = hovered
                while curr is not None:
                    if curr in _ACTIVE_CANVASES and curr.winfo_exists() and curr.winfo_ismapped():
                        target_canvas = curr
                        break
                    curr = getattr(curr, "master", None)
            except Exception:
                target_canvas = None

            # 2. Fallback: check bounding boxes in reverse registration order, prioritizing Toplevel modals
            if target_canvas is None:
                active_items = [
                    c for c in reversed(list(_ACTIVE_CANVASES.keys()))
                    if c.winfo_exists() and c.winfo_ismapped()
                ]
                # Sort so any canvas inside a Toplevel modal is checked before the main window
                active_items.sort(
                    key=lambda c: 0 if isinstance(c.winfo_toplevel(), tk.Toplevel) else 1
                )
                for canvas in active_items:
                    c_x = canvas.winfo_rootx()
                    c_y = canvas.winfo_rooty()
                    c_w = canvas.winfo_width()
                    c_h = canvas.winfo_height()
                    if c_x <= ptr_x <= (c_x + c_w) and c_y <= ptr_y <= (c_y + c_h):
                        target_canvas = canvas
                        break

            if target_canvas is not None:
                top, bottom = target_canvas.yview()
                if not (top <= 0.001 and bottom >= 0.999):
                    acc = getattr(target_canvas, "_scroll_accumulator", 0.0) + total_dy_px
                    pixel_steps = int(acc)
                    if pixel_steps != 0:
                        target_canvas._scroll_accumulator = acc - pixel_steps
                        if (pixel_steps > 0 and top <= 0.0) or (pixel_steps < 0 and bottom >= 1.0):
                            target_canvas._scroll_accumulator = 0.0
                        else:
                            target_canvas.yview_scroll(-pixel_steps, "units")
                    else:
                        target_canvas._scroll_accumulator = acc
    except Exception:
        pass

    root.after(8, lambda: _poll_scroll_queue(root))


def _on_windows_linux_wheel(event, canvas, scrollbar):
    """Pixel-smooth step scrolling for Windows, Linux, or macOS fallback without PyObjC."""
    if not canvas or not canvas.winfo_exists():
        return "break"

    try:
        top, bottom = canvas.yview()
        if top <= 0.001 and bottom >= 0.999:
            return "break"

        if IS_MAC:
            # macOS Tk MouseWheel fallback (if PyObjC is unavailable)
            delta = event.delta
            if delta != 0:
                px = int(-1 * delta * 8) or (-2 if delta > 0 else 2)
                canvas.yview_scroll(px, "units")
        elif event.delta:
            steps = int(-1 * (event.delta / 120) * WIN_WHEEL_STEP_PIXELS)
            canvas.yview_scroll(steps, "units")
        elif getattr(event, "num", None) == 4:
            canvas.yview_scroll(-WIN_WHEEL_STEP_PIXELS, "units")
        elif getattr(event, "num", None) == 5:
            canvas.yview_scroll(WIN_WHEEL_STEP_PIXELS, "units")
    except Exception:
        pass

    return "break"


def update_scrollbar_visibility(canvas, scrollbar):
    """Automatically shows/hides the scrollbar if all content fits on screen."""
    if not scrollbar or not canvas or not canvas.winfo_exists():
        return
    try:
        top, bottom = canvas.yview()
        if top <= 0.001 and bottom >= 0.999:
            if scrollbar.winfo_ismapped():
                if hasattr(scrollbar, "pack_forget"):
                    scrollbar.pack_forget()
                else:
                    scrollbar.grid_remove()
        else:
            if not scrollbar.winfo_ismapped():
                if hasattr(scrollbar, "pack"):
                    scrollbar.pack(side="right", fill="y")
                else:
                    scrollbar.grid()
    except Exception:
        pass


def enable_smooth_scroll(target_widget, scrollbar=None):
    """Thread-safe pixel-accurate smooth scrolling cross-platform."""
    global _POLL_SCHEDULED
    if isinstance(target_widget, ctk.CTkScrollableFrame):
        canvas = getattr(target_widget, "_parent_canvas", None)
        bar = getattr(target_widget, "_scrollbar", None)
        # Disable CustomTkinter's built-in jerky mousewheel handler permanently
        try:
            target_widget._mouse_wheel_all = lambda *args, **kwargs: None
            target_widget.unbind_all("<MouseWheel>")
        except Exception:
            pass
    else:
        canvas = target_widget
        bar = scrollbar

    if not canvas:
        return

    # Critical: set yscrollincrement=1 so 'units' scrolls by 1 pixel instead of 10% of screen height!
    try:
        canvas.configure(yscrollincrement=1)
    except Exception:
        pass

    canvas._scroll_accumulator = 0.0
    _ACTIVE_CANVASES[canvas] = bar

    try:
        root = target_widget._root()
    except Exception:
        root = target_widget.winfo_toplevel()

    if IS_MAC and HAS_COCOA:
        _start_cocoa_monitor()
        if not _POLL_SCHEDULED and root:
            _POLL_SCHEDULED = True
            root.after(8, lambda: _poll_scroll_queue(root))
    else:
        def _bind_wheel(e=None):
            canvas.bind_all(
                "<MouseWheel>",
                lambda ev: _on_windows_linux_wheel(ev, canvas, bar),
                add="+",
            )
            canvas.bind_all(
                "<Button-4>",
                lambda ev: _on_windows_linux_wheel(ev, canvas, bar),
                add="+",
            )
            canvas.bind_all(
                "<Button-5>",
                lambda ev: _on_windows_linux_wheel(ev, canvas, bar),
                add="+",
            )

        def _unbind_wheel(e=None):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", _bind_wheel, add="+")
        canvas.bind("<Leave>", _unbind_wheel, add="+")

    canvas.bind("<Configure>", lambda e: update_scrollbar_visibility(canvas, bar), add="+")

    def _on_destroy(event):
        if event.widget == canvas and canvas in _ACTIVE_CANVASES:
            del _ACTIVE_CANVASES[canvas]

    canvas.bind("<Destroy>", _on_destroy, add="+")
    target_widget.after(100, lambda: update_scrollbar_visibility(canvas, bar))