import { useState } from "react";
import { Modal } from "/static/js/shared/layout.js";
import { h } from "/static/js/shared/react.js";
import { PERSON_BULLET } from "../constants.js";
import { displayToPeople, peopleToDisplay } from "../utils/geometry.js";

const COLOR_ROLE_LABELS = {
  "#09519F": "Secretarios",
  "#3C8AC9": "Directores",
  "#9DC3E6": "Coordinadores, Jefes o Encargados de Departamento",
  "#797E85": "Personal Administrativo",
};

export function NodeModal({ modal, palette, onSave, onClose }) {
  const [form, setForm] = useState({ ...modal, displayName: peopleToDisplay(modal.name) });
  const insertPerson = (event) => {
    if (!(event.ctrlKey && event.key === "Enter")) return;
    event.preventDefault();
    const target = event.target;
    const start = target.selectionStart;
    const end = target.selectionEnd;
    const next = `${form.displayName.slice(0, start)}\n${PERSON_BULLET}${form.displayName.slice(end)}`;
    setForm({ ...form, displayName: next });
    requestAnimationFrame(() => {
      target.selectionStart = start + PERSON_BULLET.length + 1;
      target.selectionEnd = start + PERSON_BULLET.length + 1;
    });
  };
  const save = () => {
    const name = displayToPeople(form.displayName);
    if (!name) return;
    onSave({ ...form, name });
    onClose();
  };
  return h(
    Modal,
    { title: modal.mode === "edit" ? "Editar persona" : `Nueva persona (${modal.gridX}, ${modal.gridY})`, onClose },
    h(
      "div",
      { className: "org-node-form" },
      h("label", null, h("span", null, "Nombre(s)"), h("textarea", { value: form.displayName, onKeyDown: insertPerson, onChange: (event) => setForm({ ...form, displayName: event.target.value }) })),
      h("p", { className: "org-node-hint" }, "Ctrl + Enter agrega otra persona con viñeta nueva"),
      h("label", null, h("span", null, "Cargo"), h("input", { value: form.role, onChange: (event) => setForm({ ...form, role: event.target.value }) })),
      h(
        "div",
        { className: "org-color-field" },
        h("span", null, "Color"),
        h(
          "div",
          { className: "org-swatches" },
          palette.map((item) =>
            h("button", {
              key: item.value,
              className: item.value === form.color ? "org-color-option selected" : "org-color-option",
              title: item.label,
              onClick: () => setForm({ ...form, color: item.value }),
            }, h("span", { className: "org-swatch", style: { background: item.value } }), h("span", null, COLOR_ROLE_LABELS[item.value] || item.label))
          )
        )
      ),
      h("div", { className: "modal-actions" }, h("button", { onClick: onClose }, "Cancelar"), h("button", { onClick: save }, "Guardar"))
    )
  );
}
