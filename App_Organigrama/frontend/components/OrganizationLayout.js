import { h } from "/static/js/shared/react.js";

export function MetadataStrip({ document, setDocument }) {
  return h(
    "section",
    { className: "org-form-strip" },
    h("label", null, h("span", null, "Titulo del organigrama"), h("input", { value: document.title, placeholder: "Titulo del organigrama", onChange: (event) => setDocument({ ...document, title: event.target.value }) })),
    h("label", null, h("span", null, "Periodo"), h("input", { value: document.period, placeholder: "ej. Enero - Marzo 2026", onChange: (event) => setDocument({ ...document, period: event.target.value }) }))
  );
}

export function ToolStrip({ document, setDocument, selected, deleteSelection, resetSelectedRoute, panCamera }) {
  return h(
    "section",
    { className: "org-tool-strip" },
    h("label", { className: "org-check" }, h("input", { type: "checkbox", checked: document.show_logos, onChange: (event) => setDocument({ ...document, show_logos: event.target.checked }) }), h("span", null, "Escudos")),
    h("button", { className: "org-danger", onClick: deleteSelection, disabled: !selected.id }, "Eliminar seleccion"),
    h("button", { onClick: resetSelectedRoute, disabled: selected.type !== "connection" }, "Restaurar ruta automatica"),
    h("div", { className: "org-nudge" }, h("button", { onClick: () => panCamera(0, 80) }, "↑"), h("button", { onClick: () => panCamera(80, 0) }, "←"), h("button", { onClick: () => panCamera(0, -80) }, "↓"), h("button", { onClick: () => panCamera(-80, 0) }, "→"))
  );
}

export function CanvasStage({ canvasRef, onMouseDown, onMouseMove, onMouseUp, onMouseLeave, onDoubleClick, onWheel }) {
  return h(
    "section",
    { className: "org-canvas-frame" },
    h("canvas", {
      ref: canvasRef,
      className: "org-canvas",
      onMouseDown,
      onMouseMove,
      onMouseUp,
      onMouseLeave,
      onDoubleClick,
      onContextMenu: (event) => event.preventDefault(),
      onWheel,
    })
  );
}

export function BottomBar({ focusNode, undo, redo, undoStack, redoStack, status, viewport, zoomBy }) {
  return h(
    "section",
    { className: "org-bottom-bar" },
    h("button", { className: "org-focus-button", onClick: () => focusNode() }, "Enfocar ultimo"),
    h("button", { className: "org-icon-button", onClick: undo, disabled: undoStack.length === 0 }, "↶"),
    h("button", { className: "org-icon-button", onClick: redo, disabled: redoStack.length === 0 }, "↷"),
    h("span", { className: status.error ? "org-status error" : "org-status" }, status.message),
    h("div", { className: "org-zoom" }, h("span", null, "Zoom"), h("button", { onClick: () => zoomBy(-0.1) }, "-"), h("span", null, `${Math.round(viewport.zoom * 100)}%`), h("button", { onClick: () => zoomBy(0.1) }, "+"))
  );
}
