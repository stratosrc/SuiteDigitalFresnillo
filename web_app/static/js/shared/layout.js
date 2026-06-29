import { h, React } from "./react.js";
import { moduleTitles, modules } from "./constants.js";
import { navigate } from "./helpers.js";

export function Shell({ path }) {
  const activeId = modules.find((item) => item.path === path)?.id || "home";
  const title = moduleTitles[path] || "Suite Digital Fresnillo";
  return h(
    React.Fragment,
    null,
    h(
      "header",
      { className: "suite-header" },
      h(
        "button",
        { className: "brand-button", onClick: () => navigate("/") },
        h("img", { src: "/assets/SuiteIcon.png", alt: "" }),
        h("span", null, title)
      ),
      h(
        "nav",
        { className: "suite-tabs" },
        h(Tab, { active: activeId === "home", path: "/", label: "Inicio" }),
        modules.map((item) => h(Tab, { key: item.id, active: activeId === item.id, path: item.path, label: item.name }))
      )
    )
  );
}

export function Modal({ title, children, onClose, wide = false }) {
  return h(
    "div",
    { className: "modal-backdrop", role: "dialog", "aria-modal": "true" },
    h(
      "section",
      { className: wide ? "modal-window wide" : "modal-window" },
      h("div", { className: "modal-header" }, h("h2", null, title), h("button", { onClick: onClose }, "Cerrar")),
      h("div", { className: "modal-body" }, children)
    )
  );
}

export function Tab({ active, path, label }) {
  return h(
    "button",
    { className: active ? "tab active" : "tab", onClick: () => navigate(path) },
    label
  );
}

export function ToolFrame({ title, subtitle, children, workspace, status, actions }) {
  return h(
    "main",
    { className: "tool-window" },
    h(
      "aside",
      { className: "left-panel" },
      h("div", { className: "panel-title" }, h("h1", null, title), h("p", null, subtitle)),
      children,
      status ? h("p", { className: status.error ? "status-text error" : "status-text" }, status.message) : null
    ),
    h(
      "section",
      { className: "right-panel" },
      h("div", { className: "workspace-toolbar" }, h("span", null, title), h("div", { className: "toolbar-actions" }, actions)),
      workspace
    )
  );
}

export function Field({ label, children }) {
  return h("label", { className: "field" }, h("span", null, label), children);
}
