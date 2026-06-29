import { Modal } from "/static/js/shared/layout.js";
import { h } from "/static/js/shared/react.js";

export function HelpModal({ content, onClose }) {
  return h(
    Modal,
    { title: content?.title || "Ayuda", onClose },
    h("h3", { className: "modal-heading" }, content?.heading || "Guía de uso"),
    h(
      "div",
      { className: "help-sections" },
      (content?.sections || []).map(([title, bullets]) =>
        h(
          "section",
          { key: title },
          h("h4", null, title),
          bullets.map((bullet) => h("p", { key: bullet }, `• ${bullet}`))
        )
      )
    )
  );
}
