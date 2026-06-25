import tkinter as tk

from components.styles.styles import CTK_FONT_FAMILY, SURFACE_BG, TEXT_DARK


class Tooltip:
    _active_tooltip: "Tooltip | None" = None

    def __init__(self, widget, text: str, delay_ms: int = 450, show_when_disabled: bool = False):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self.show_when_disabled = show_when_disabled
        self._after_id = None
        self._window = None
        self._bound_widgets = set()

        self._bind_hover_targets()
        widget.after_idle(self._bind_hover_targets)

    def show_now(self, _event=None):
        self._cancel()
        self._show()

    def hide(self, _event=None):
        self._hide()

    def _bind_hover_targets(self):
        for target in self._iter_widgets(self.widget):
            target_id = str(target)
            if target_id in self._bound_widgets:
                continue
            self._bound_widgets.add(target_id)
            target.bind("<Enter>", self._schedule, add=True)
            target.bind("<Leave>", self._hide_if_pointer_outside, add=True)
            target.bind("<ButtonPress>", self._hide, add=True)
            target.bind("<FocusOut>", self._hide, add=True)
            target.bind("<Unmap>", self._hide, add=True)
            target.bind("<Destroy>", self._hide, add=True)

    def _iter_widgets(self, widget):
        yield widget
        try:
            children = widget.winfo_children()
        except tk.TclError:
            return
        for child in children:
            yield from self._iter_widgets(child)

    def _schedule(self, _event=None):
        self._cancel()
        if not self._can_show():
            return
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _show(self):
        if self._window is not None or not self.text or not self._can_show():
            return
        active_tooltip = Tooltip._active_tooltip
        if active_tooltip is not None and active_tooltip is not self:
            active_tooltip._hide()

        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6

        self._window = tk.Toplevel(self.widget)
        self._window.wm_overrideredirect(True)
        self._window.transient(self.widget.winfo_toplevel())
        self._window.wm_geometry(f"+{x}+{y}")
        self._window.lift()
        self._window.attributes("-topmost", True)
        self._window.after_idle(self._release_topmost)
        self._window.bind("<FocusOut>", self._hide, add=True)
        self._window.bind("<ButtonPress>", self._hide, add=True)

        label = tk.Label(
            self._window,
            text=self.text,
            bg=SURFACE_BG,
            fg=TEXT_DARK,
            relief=tk.SOLID,
            borderwidth=1,
            padx=8,
            pady=4,
            font=(CTK_FONT_FAMILY, 9),
        )
        label.pack()
        Tooltip._active_tooltip = self

    def _release_topmost(self):
        if self._window is None:
            return
        try:
            self._window.attributes("-topmost", False)
        except tk.TclError:
            pass

    def _hide_if_pointer_outside(self, _event=None):
        if self._pointer_inside_widget():
            return
        self._hide()

    def _pointer_inside_widget(self) -> bool:
        try:
            x = self.widget.winfo_pointerx()
            y = self.widget.winfo_pointery()
            left = self.widget.winfo_rootx()
            top = self.widget.winfo_rooty()
            right = left + self.widget.winfo_width()
            bottom = top + self.widget.winfo_height()
            return left <= x <= right and top <= y <= bottom
        except tk.TclError:
            return False

    def _hide(self, _event=None):
        self._cancel()
        if self._window is not None:
            try:
                self._window.destroy()
            except tk.TclError:
                pass
            self._window = None
        if Tooltip._active_tooltip is self:
            Tooltip._active_tooltip = None

    def _cancel(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def _can_show(self) -> bool:
        try:
            if not self.widget.winfo_exists() or not self.widget.winfo_ismapped():
                return False
            return self.show_when_disabled or str(self.widget.cget("state")) != tk.DISABLED
        except tk.TclError:
            return False


__all__ = ["Tooltip"]
