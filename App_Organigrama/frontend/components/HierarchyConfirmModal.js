import { Modal } from "/static/js/shared/layout.js";
import { h } from "/static/js/shared/react.js";

export function HierarchyConfirmModal({ sourceLabel, targetLabel, onConfirm, onCancel }) {
  return h(
    Modal,
    { title: "Conexión jerárquica inversa", onClose: onCancel },
    h(
      "div",
      { className: "org-hierarchy-warning" },
      h("p", null, "Estás conectando de una jerarquía menor hacia una jerarquía mayor."),
      h("p", null, h("strong", null, "Origen: "), sourceLabel),
      h("p", null, h("strong", null, "Destino: "), targetLabel),
      h("p", null, "Esto podría invertir el sentido natural del organigrama. ¿Quieres continuar?"),
      h("div", { className: "modal-actions" }, h("button", { onClick: onCancel }, "Cancelar"), h("button", { onClick: onConfirm }, "Continuar"))
    )
  );
}
