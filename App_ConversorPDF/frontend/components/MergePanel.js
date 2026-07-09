import { h, React } from "/static/js/shared/react.js";
import { humanFileSize, pdfOnlyTypes } from "../constants.js";
import { DropPanel } from "./DropPanel.js";

export function MergePanel({ entries, onAddFiles, onMerge, onRemoveEntry, onReorder }) {
  const [dragIndex, setDragIndex] = React.useState(null);

  const finishDrag = (targetIndex) => {
    if (dragIndex === null) return;
    onReorder(dragIndex, targetIndex);
    setDragIndex(null);
  };

  return h(
    "section",
    { className: "merge-workspace" },
    h(
      "div",
      { className: "merge-list-panel" },
      h("h2", null, "Orden de los archivos"),
      entries.length
        ? h(
            "div",
            { className: "merge-list" },
            entries.map((entry, index) =>
              h(
                "article",
                {
                  key: entry.id,
                  className: dragIndex === index ? "merge-row dragging" : "merge-row",
                  draggable: true,
                  onDragStart: () => setDragIndex(index),
                  onDragOver: (event) => event.preventDefault(),
                  onDrop: () => finishDrag(index),
                  onDragEnd: () => setDragIndex(null),
                },
                h("span", { className: "merge-index" }, index + 1),
                h("div", null, h("strong", null, entry.file.name), h("span", null, humanFileSize(entry.file.size))),
                h("button", { type: "button", onClick: () => onRemoveEntry(entry.id) }, "Quitar")
              )
            ),
            h(
              "div",
              {
                className: "merge-drop-end",
                onDragOver: (event) => event.preventDefault(),
                onDrop: () => finishDrag(entries.length),
              },
              "Soltar al final"
            )
          )
        : h(
            DropPanel,
            { accept: pdfOnlyTypes, className: "merge-empty-drop", onFiles: onAddFiles },
            h("strong", null, "Arrastra aquí dos o más PDFs"),
            h("strong", null, "o haz clic para seleccionarlos")
          ),
      entries.length
        ? h("button", { type: "button", className: "merge-add-button", onClick: () => document.querySelector("#merge-file-input")?.click() }, "Agregar PDFs")
        : null,
      h("input", {
        id: "merge-file-input",
        type: "file",
        accept: pdfOnlyTypes,
        multiple: true,
        className: "hidden-file-input",
        onChange: (event) => {
          onAddFiles(Array.from(event.target.files || []));
          event.target.value = "";
        },
      })
    ),
    h(
      "div",
      { className: "merge-action-panel" },
      h("h2", null, "Unir PDFs"),
      h("p", null, "Arrastra los elementos de la lista para cambiar el orden."),
      h("p", null, "Las páginas se unirán de arriba hacia abajo."),
      h("strong", null, `${entries.length} archivos seleccionados`),
      h(
        "button",
        { type: "button", disabled: entries.length < 2, onClick: onMerge },
        "Unir y guardar"
      )
    )
  );
}
