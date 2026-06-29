import { useState } from "react";
import { Modal } from "/static/js/shared/layout.js";
import { h } from "/static/js/shared/react.js";

const tabs = [
  ["general", "General"],
  ["reserved", "Información Reservada"],
  ["confidential", "Información Confidencial"],
  ["other_law", "Otra Ley"],
];

export function RedactionModal({ concepts, form, setForm, histories, onAccept, onCancel }) {
  const [tab, setTab] = useState(form.classification || "general");
  const [query, setQuery] = useState("");
  const filteredConcepts = concepts.filter((item) => `${item.id}. ${item.name}`.toLowerCase().includes(query.toLowerCase()));
  const updateTab = (nextTab) => {
    const shouldClearReservedFields =
      (tab === "reserved" && nextTab === "confidential") || (tab === "confidential" && nextTab === "reserved");
    setTab(nextTab);
    setForm({
      ...form,
      classification: nextTab,
      ...(shouldClearReservedFields ? { legal_basis: "", reason: "", rows: "1", paragraphs: "1" } : {}),
    });
  };
  const update = (key, value) => setForm({ ...form, [key]: value });
  const field = (label, key, props = {}) =>
    h(
      "label",
      { className: "redaction-row" },
      h("span", null, label),
      h("input", { value: form[key] || "", onChange: (event) => update(key, event.target.value), ...props })
    );
  const historyBox = (kind) =>
    h(
      "div",
      { className: "redaction-history" },
      (histories?.[kind] || []).map((entry, index) =>
        h(
          "button",
          {
            key: index,
            onClick: () => setForm({ ...form, ...entry, classification: kind }),
          },
          kind === "other_law"
            ? `${entry.object || "Sin objeto"} | ${entry.law || "Sin ley"}`
            : `${entry.legal_basis || "Sin fundamento"} | ${entry.reason || "Sin motivo"}`
        )
      )
    );

  return h(
    Modal,
    { title: "Configurar datos del rectángulo", onClose: onCancel },
    h("h3", { className: "redaction-heading" }, "Configurar"),
    h(
      "div",
      { className: "redaction-tabs" },
      tabs.map(([id, label]) => h("button", { key: id, className: tab === id ? "active" : "", onClick: () => updateTab(id) }, label))
    ),
    tab === "general"
      ? h(
          "div",
          { className: "redaction-form" },
          h("label", { className: "redaction-stack" }, h("span", null, "Buscar Concepto:"), h("input", { value: query, onChange: (event) => setQuery(event.target.value) })),
          h(
            "div",
            { className: "concept-list" },
            filteredConcepts.map((item) =>
              h("button", { key: item.id, className: String(item.id) === String(form.concept_id) ? "selected" : "", onClick: () => update("concept_id", String(item.id)) }, `${item.id}. ${item.name}`)
            )
          ),
          field("Renglones:", "rows", { type: "number", min: "1" }),
          field("Párrafos:", "paragraphs", { type: "number", min: "1" })
        )
      : null,
    tab === "reserved" || tab === "confidential"
      ? h(
          "div",
          { className: "redaction-form" },
          field("Fundamento legal", "legal_basis"),
          field("En virtud tratarse de", "reason"),
          field("Cantidad de párrafos", "paragraphs", { type: "number", min: "1" }),
          field("Cantidad de renglones", "rows", { type: "number", min: "1" }),
          h("label", { className: "redaction-stack" }, h("span", null, "Historial"), historyBox(tab))
        )
      : null,
    tab === "other_law"
      ? h(
          "div",
          { className: "redaction-form" },
          field("Objeto", "object", { placeholder: "Ej: Sueldo Neto, Fotografía, Convenio..." }),
          field("Artículos", "articles", { placeholder: "Ej: Artículo 45 Fracción II, Art. 12..." }),
          field("Ley", "law", { placeholder: "Ej: Ley de Disciplina Financiera..." }),
          field("Cantidad de párrafos", "paragraphs", { type: "number", min: "1" }),
          field("Cantidad de renglones", "rows", { type: "number", min: "1" }),
          h("label", { className: "redaction-stack" }, h("span", null, "Historial"), historyBox("other_law"))
        )
      : null,
    h("div", { className: "modal-actions" }, h("button", { onClick: onAccept }, "Aceptar"), h("button", { onClick: onCancel }, "Cancelar"))
  );
}
