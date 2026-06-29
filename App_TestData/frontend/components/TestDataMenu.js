import { navigate } from "/static/js/shared/helpers.js";
import { h } from "/static/js/shared/react.js";

export function TestDataMenu({ fileMenuOpen, setFileMenuOpen, onNew, onLoadProject, onSaveProject, onExportPdf, onOpenCatalogue, onOpenHelp }) {
  return h(
    "section",
    { className: "testdata-menu" },
    h(
      "div",
      { className: "file-menu-wrap" },
      h("button", { onClick: () => setFileMenuOpen(!fileMenuOpen) }, "Archivo"),
      fileMenuOpen
        ? h(
            "div",
            { className: "file-dropdown" },
            h("button", { onClick: () => (setFileMenuOpen(false), onNew()) }, "Nuevo"),
            h("button", { onClick: () => (setFileMenuOpen(false), onLoadProject()) }, "Cargar proyecto"),
            h("button", { onClick: () => (setFileMenuOpen(false), onSaveProject()) }, "Guardar proyecto"),
            h("button", { onClick: () => (setFileMenuOpen(false), onExportPdf()) }, "Exportar PDF")
          )
        : null
    ),
    h("button", { onClick: onOpenCatalogue }, "Catálogo"),
    h("button", { onClick: onOpenHelp }, "Ayuda"),
    h("button", { className: "exit-button", onClick: () => navigate("/") }, "Salir")
  );
}
