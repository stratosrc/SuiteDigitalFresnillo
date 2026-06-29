import { h } from "/static/js/shared/react.js";

export function TestDataToolbar({ onUndo, onRedo, onDelete, canUndo, canRedo, selectedRectId }) {
  return h(
    "section",
    { className: "testdata-toolbar" },
    h("button", { className: "icon-button", title: "Deshacer", onClick: onUndo, disabled: !canUndo }, h("img", { src: "/testdata-assets/undo.png", alt: "" })),
    h("button", { className: "icon-button", title: "Rehacer", onClick: onRedo, disabled: !canRedo }, h("img", { src: "/testdata-assets/redo.png", alt: "" })),
    h("button", { className: "icon-button danger", title: "Eliminar", onClick: onDelete, disabled: !selectedRectId }, h("img", { src: "/testdata-assets/eliminar.png", alt: "" }))
  );
}
