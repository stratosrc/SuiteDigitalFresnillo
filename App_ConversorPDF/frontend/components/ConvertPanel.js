import { h } from "/static/js/shared/react.js";
import { acceptedConvertTypes, assetUrl, humanFileSize } from "../constants.js";
import { DropPanel } from "./DropPanel.js";
import { HoverIcon } from "./HoverIcon.js";

const selectionPlaceholder = (name) =>
  /\.(xls|xlsx|ods|csv)$/i.test(name)
    ? "Hojas del libro a exportar, ej. 2-4 o 1, 4-6. Dejar vacio para todas."
    : "Paginas a exportar, ej. 2-4 o 1, 4-6. Dejar vacio para convertir todas.";

export function ConvertPanel({
  entries,
  outputs,
  onAddFiles,
  onDownloadAll,
  onDownloadOutput,
  onRemoveEntry,
  onSelectionChange,
  onToggleSplit,
}) {
  return h(
    "section",
    { className: "convert-workspace" },
    h(
      "div",
      { className: "convert-upload-panel" },
      entries.length
        ? h(
            "div",
            { className: "convert-source-list" },
            h(
              "div",
              { className: "convert-source-scroll" },
              entries.map((entry) =>
                h(
                  "article",
                  { key: entry.id, className: "convert-source-card" },
                  h(
                    "div",
                    { className: "convert-source-main" },
                    h("button", { type: "button", onClick: () => onRemoveEntry(entry.id), title: "Quitar" }, "X"),
                    h(
                      "div",
                      null,
                      h("strong", null, entry.file.name),
                      h("span", null, humanFileSize(entry.file.size))
                    ),
                    h(
                      "button",
                      {
                        type: "button",
                        className: `convert-separate-toggle${entry.splitOutput ? " active" : ""}`,
                        title: "Separar hojas o paginas en archivos individuales",
                        "aria-pressed": entry.splitOutput,
                        onClick: () => onToggleSplit(entry.id),
                      },
                      h("img", { src: assetUrl(entry.splitOutput ? "separate_on.png" : "separate.png"), alt: "" })
                    )
                  ),
                  h("input", {
                    value: entry.selection,
                    placeholder: selectionPlaceholder(entry.file.name),
                    onChange: (event) => onSelectionChange(entry.id, event.target.value),
                  })
                )
              )
            )
          )
        : h(
            DropPanel,
            { accept: acceptedConvertTypes, onFiles: onAddFiles },
            h(HoverIcon, { base: "upload.png", hover: "upload_hover.png" }),
            h("strong", null, "Arrastra archivos aqui o haz clic para comenzar")
          )
    ),
    h(
      "div",
      { className: "convert-ready-panel" },
      outputs.length
        ? h(
            "div",
            { className: "convert-output-area" },
            h(
              "div",
              { className: "convert-output-list" },
              outputs.map((output) =>
                h(
                  "article",
                  { key: output.id, className: "convert-output-row" },
                  h("strong", null, output.filename),
                  h(
                    "button",
                    { type: "button", title: "Descargar", onClick: () => onDownloadOutput(output) },
                    h("img", { src: assetUrl("dl.png"), alt: "" })
                  )
                )
              )
            ),
            h("button", { type: "button", className: "convert-download-all", onClick: onDownloadAll }, "Descargar todos")
          )
        : h(
            "div",
            { className: "convert-empty-ready" },
            h(HoverIcon, { base: "download.png", hover: "download_hover.png" }),
            h("strong", null, "Los archivos listos para convertir apareceran aqui")
          )
    )
  );
}
