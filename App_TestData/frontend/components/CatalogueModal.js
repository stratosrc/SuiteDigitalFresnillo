import { Modal } from "/static/js/shared/layout.js";
import { h } from "/static/js/shared/react.js";

export function CatalogueModal({ sections, onClose }) {
  return h(
    Modal,
    { title: "Catálogo de Conceptos", onClose, wide: true },
    h(
      "div",
      { className: "catalogue-columns" },
      (sections || []).map((section) =>
        h(
          "section",
          { key: section.title, className: "catalogue-column" },
          h("h3", null, section.title),
          h(
            "div",
            { className: "catalogue-list" },
            section.items.map((item) => h("p", { key: item.id }, `${item.id}. ${item.name}`))
          )
        )
      )
    )
  );
}
