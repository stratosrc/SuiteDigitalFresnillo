import { h } from "/static/js/shared/react.js";
import { Modal } from "/static/js/shared/layout.js";

export function HelpModal({ help, onClose }) {
  return h(
    Modal,
    { title: help?.title || "Ayuda de Directorio", onClose },
    h("h3", { className: "modal-heading" }, help?.heading || "Guia de uso"),
    h(
      "div",
      { className: "help-sections" },
      (help?.sections || []).map((section) =>
        h(
          "section",
          { key: section.title },
          h("h4", null, section.title),
          section.items.map((item) => h("p", { key: item }, `\u2022 ${item}`))
        )
      )
    )
  );
}
