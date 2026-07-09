import { navigate } from "/static/js/shared/helpers.js";
import { h } from "/static/js/shared/react.js";

export function ConverterShell({ activeTab, onNew, onHelp, onTabChange, children, status }) {
  return h(
    "main",
    { className: "converter-app" },
    h(
      "section",
      { className: "converter-menu" },
      h("button", { type: "button", onClick: onNew }, "Nuevo"),
      h("button", { type: "button", onClick: onHelp }, "Ayuda"),
      h("button", { type: "button", className: "converter-exit", onClick: () => navigate("/") }, "Salir")
    ),
    h(
      "section",
      { className: "converter-tabs" },
      h(
        "button",
        { type: "button", className: activeTab === "convert" ? "active" : "", onClick: () => onTabChange("convert") },
        "Convertir a PDF"
      ),
      h(
        "button",
        { type: "button", className: activeTab === "merge" ? "active" : "", onClick: () => onTabChange("merge") },
        "Unir PDFs"
      )
    ),
    children,
    status?.message ? h("div", { className: status.error ? "converter-status error" : "converter-status" }, status.message) : null
  );
}
