import { h, React } from "/static/js/shared/react.js";
import { formatEmailOnBlur } from "../constants.js";
import { IconButton } from "./IconButton.js";
import { PositionInput } from "./PositionInput.js";

export function PersonRow({
  areaIndex,
  areaOptions,
  person,
  personIndex,
  canMoveDown,
  canMoveUp,
  canRemove,
  onMove,
  onPositionCommit,
  onRemove,
  onTransfer,
  onUpdate,
}) {
  const [transferOpen, setTransferOpen] = React.useState(false);
  const transferTargets = areaOptions.filter((area) => area.index !== areaIndex);

  return h(
    "div",
    { className: "person-row" },
    h(
      "div",
      { className: "transfer-cell" },
      h(
        "button",
        {
          type: "button",
          className: "transfer-button",
          disabled: transferTargets.length === 0,
          title: "Transferir a otra area",
          onClick: () => setTransferOpen((value) => !value),
        },
        "▼"
      ),
      transferOpen
        ? h(
            "div",
            { className: "transfer-menu" },
            transferTargets.map((target) =>
              h(
                "button",
                {
                  type: "button",
                  key: target.index,
                  onClick: () => {
                    setTransferOpen(false);
                    onTransfer(target.index);
                  },
                },
                `${target.index + 1}. ${target.name || "Area sin nombre"}`
              )
            )
          )
        : null
    ),
    h(PositionInput, {
      className: "person-number",
      value: personIndex + 1,
      ariaLabel: "Posicion del colaborador",
      onCommit: onPositionCommit,
    }),
    h("input", {
      value: person.rank,
      placeholder: "Rango / Clave / Nivel",
      onChange: (event) => onUpdate({ rank: event.target.value }),
    }),
    h("input", {
      value: person.name,
      placeholder: "Nombre",
      onChange: (event) => onUpdate({ name: event.target.value }),
    }),
    h("input", {
      value: person.position,
      placeholder: "Cargo",
      onChange: (event) => onUpdate({ position: event.target.value }),
    }),
    h("input", {
      value: person.email,
      placeholder: "Correo electronico",
      onBlur: (event) => onUpdate({ email: formatEmailOnBlur(event.target.value) }),
      onChange: (event) => onUpdate({ email: event.target.value }),
    }),
    h("input", {
      value: person.start_date,
      placeholder: "dd/mm/aaaa",
      onChange: (event) => onUpdate({ start_date: event.target.value }),
    }),
    h(
      "div",
      { className: "person-actions" },
      h(IconButton, {
        icon: "up.png",
        hoverIcon: "up_hover.png",
        label: "Subir colaborador",
        disabled: !canMoveUp,
        onClick: () => onMove(-1),
      }),
      h(IconButton, {
        icon: "down.png",
        hoverIcon: "down_hover.png",
        label: "Bajar colaborador",
        disabled: !canMoveDown,
        onClick: () => onMove(1),
      }),
      h(IconButton, {
        icon: "minus.png",
        hoverIcon: "minus_hover.png",
        label: "Eliminar colaborador",
        disabled: !canRemove,
        onClick: onRemove,
      })
    )
  );
}
