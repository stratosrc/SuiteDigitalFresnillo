import { Modal } from "/static/js/shared/layout.js";
import { h } from "/static/js/shared/react.js";

export function HelpModal({ content, onClose }) {
  return h(
    Modal,
    { title: content?.title || "Ayuda de Organigramas", onClose, wide: true },
    h(
      "div",
      { className: "org-help" },
      (content?.sections || []).map((section) =>
        h("section", { key: section.title }, h("h3", null, section.title), section.items.map((item) => h("p", { key: item }, item)))
      )
    )
  );
}
