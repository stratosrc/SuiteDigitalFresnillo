import { Modal } from "/static/js/shared/layout.js";
import { h } from "/static/js/shared/react.js";

const OPTIONS = [
  { value: "horizontal", label: "Horizontal", icon: "/organigrama-assets/horizontal.png" },
  { value: "vertical", label: "Vertical", icon: "/organigrama-assets/vertical.png" },
];

export function OrientationModal({ current, onSelect, onClose }) {
  return h(
    Modal,
    { title: "Orientación", onClose },
    h(
      "div",
      { className: "org-orientation-modal" },
      h("h3", null, "Seleccione la orientación"),
      h(
        "div",
        { className: "org-orientation-options" },
        OPTIONS.map((option) =>
          h(
            "button",
            {
              key: option.value,
              className: option.value === current ? "org-orientation-option selected" : "org-orientation-option",
              onClick: () => onSelect(option.value),
            },
            h("img", { className: "org-orientation-icon", src: option.icon, alt: "" }),
            h("span", null, option.label)
          )
        )
      ),
      h("div", { className: "org-orientation-actions" }, h("button", { onClick: onClose }, "Cancelar"))
    )
  );
}
