import { Modal } from "/static/js/shared/layout.js";
import { h } from "/static/js/shared/react.js";

export function HelpModal({ content, onClose }) {
  return h(
    Modal,
    { title: content?.title || "Ayuda de Organigramas", onClose },
    h("h3", { className: "modal-heading" }, content?.heading || "Guia de uso"),
    h(
      "div",
      { className: "help-sections" },
      (content?.sections || []).map((section) =>
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
