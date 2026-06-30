import { navigate } from "/static/js/shared/helpers.js";
import { h } from "/static/js/shared/react.js";

export function OrganizationMenu({ fileMenuOpen, setFileMenuOpen, onNew, onSaveProject, onLoadProject, onExportPdf, onHelp }) {
  return h(
    "section",
    { className: "org-menu" },
    h(
      "div",
      { className: "org-file-menu" },
      h("button", { onClick: () => setFileMenuOpen(!fileMenuOpen) }, "Archivo"),
      fileMenuOpen
        ? h(
            "div",
            { className: "org-file-dropdown" },
            h("button", { onClick: () => (setFileMenuOpen(false), onNew()) }, "Nuevo"),
            h("button", { onClick: () => (setFileMenuOpen(false), onSaveProject()) }, "Guardar proyecto"),
            h("button", { onClick: () => (setFileMenuOpen(false), onLoadProject()) }, "Cargar proyecto"),
            h("button", { onClick: () => (setFileMenuOpen(false), onExportPdf()) }, "Exportar PDF")
          )
        : null
    ),
    h("button", { onClick: onHelp }, "Ayuda"),
    h("button", { className: "org-exit-button", onClick: () => navigate("/") }, "Salir")
  );
}
