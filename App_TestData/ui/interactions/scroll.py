"""Mouse wheel helpers for scrolling and zooming."""

CTRL_MASK = 0x0004


def setup_mousewheel_scroll(
    canvas_widget,
    has_document=None,
    on_zoom_in=None,
    on_zoom_out=None,
):
    """Bind cross-platform wheel support to a canvas widget."""
    canvas_widget.bind(
        "<MouseWheel>",
        lambda event: on_mousewheel(
            canvas_widget,
            event,
            has_document=has_document,
            on_zoom_in=on_zoom_in,
            on_zoom_out=on_zoom_out,
        ),
    )
    canvas_widget.bind(
        "<Button-4>",
        lambda event: on_mousewheel(
            canvas_widget,
            event,
            has_document=has_document,
            on_zoom_in=on_zoom_in,
            on_zoom_out=on_zoom_out,
        ),
    )
    canvas_widget.bind(
        "<Button-5>",
        lambda event: on_mousewheel(
            canvas_widget,
            event,
            has_document=has_document,
            on_zoom_in=on_zoom_in,
            on_zoom_out=on_zoom_out,
        ),
    )
    canvas_widget.bind(
        "<Control-Button-4>",
        lambda event: on_mousewheel(
            canvas_widget,
            event,
            has_document=has_document,
            on_zoom_in=on_zoom_in,
            on_zoom_out=on_zoom_out,
        ),
    )
    canvas_widget.bind(
        "<Control-Button-5>",
        lambda event: on_mousewheel(
            canvas_widget,
            event,
            has_document=has_document,
            on_zoom_in=on_zoom_in,
            on_zoom_out=on_zoom_out,
        ),
    )


def on_mousewheel(
    canvas_widget,
    event,
    has_document=None,
    on_zoom_in=None,
    on_zoom_out=None,
):
    """Handle normalized scroll and Ctrl+wheel zoom gestures."""
    if has_document is not None and not has_document():
        return

    wheel_action = get_wheel_action(
        event_num=getattr(event, "num", None),
        event_delta=getattr(event, "delta", 0),
        event_state=getattr(event, "state", 0),
    )

    if wheel_action == "zoom_in" and on_zoom_in is not None:
        on_zoom_in()
        return
    if wheel_action == "zoom_out" and on_zoom_out is not None:
        on_zoom_out()
        return

    scroll_direction = get_wheel_direction(
        event_num=getattr(event, "num", None),
        event_delta=getattr(event, "delta", 0),
    )
    if scroll_direction:
        canvas_widget.yview_scroll(scroll_direction, "units")


def get_wheel_action(event_num=None, event_delta=0, event_state=0) -> str | None:
    """Resolve whether a wheel event should trigger zoom instead of scroll."""
    if not bool(event_state & CTRL_MASK):
        return None
    if event_num == 4 or event_delta > 0:
        return "zoom_in"
    if event_num == 5 or event_delta < 0:
        return "zoom_out"
    return None


def get_wheel_direction(event_num=None, event_delta=0) -> int:
    """Normalize wheel direction across Windows, macOS, and Linux."""
    if event_num == 4:
        return -1
    if event_num == 5:
        return 1
    if not event_delta:
        return 0

    direction = int(-1 * (event_delta / 120))
    if direction == 0:
        return -1 if event_delta > 0 else 1
    return direction
