import { h } from "/static/js/shared/react.js";
import { PersonRow } from "./PersonRow.js";
import { IconButton } from "./IconButton.js";
import { PositionInput } from "./PositionInput.js";

export function AreaSection({
  area,
  areaIndex,
  areaOptions,
  canMoveDown,
  canMoveUp,
  canRemove,
  onAddPerson,
  onAreaPositionCommit,
  onMoveArea,
  onMovePerson,
  onRemoveArea,
  onRemovePerson,
  onTransferPerson,
  onUpdateArea,
  onUpdatePerson,
}) {
  return h(
    "section",
    { className: "area-card" },
    h(
      "div",
      { className: "area-title-row" },
      h(PositionInput, {
        className: "area-number",
        value: areaIndex + 1,
        ariaLabel: "Posicion del area",
        onCommit: onAreaPositionCommit,
      }),
      h("input", {
        className: "area-name",
        value: area.name,
        placeholder: "Agregar Area, ej. Jefatura de Gobierno Digital",
        onChange: (event) => onUpdateArea({ name: event.target.value }),
      }),
      h(
        "div",
        { className: "area-actions" },
        h(IconButton, {
          icon: "up.png",
          hoverIcon: "up_hover.png",
          label: "Subir area",
          disabled: !canMoveUp,
          onClick: () => onMoveArea(-1),
        }),
        h(IconButton, {
          icon: "down.png",
          hoverIcon: "down_hover.png",
          label: "Bajar area",
          disabled: !canMoveDown,
          onClick: () => onMoveArea(1),
        }),
        h(IconButton, {
          icon: "x.png",
          hoverIcon: "x_hover.png",
          label: "Eliminar area",
          disabled: !canRemove,
          onClick: onRemoveArea,
        })
      )
    ),
    h(
      "div",
      { className: "person-header" },
      h("div", null),
      h("span", { className: "person-header-index" }, "#"),
      h("span", null, "Rango / Clave / Nivel"),
      h("span", null, "Nombre"),
      h("span", null, "Cargo"),
      h("span", null, "Correo electronico"),
      h("span", null, "Fecha de Alta"),
      h("div", null)
    ),
    h(
      "div",
      { className: "person-list" },
      area.personnel.map((person, personIndex) =>
        h(PersonRow, {
          key: person.localId || personIndex,
          areaIndex,
          areaOptions,
          person,
          personIndex,
          canMoveDown: personIndex < area.personnel.length - 1,
          canMoveUp: personIndex > 0,
          canRemove: area.personnel.length > 1,
          onMove: (direction) => onMovePerson(personIndex, direction),
          onPositionCommit: (value) => onMovePerson(personIndex, value - 1 - personIndex),
          onRemove: () => onRemovePerson(personIndex),
          onTransfer: (targetAreaIndex) => onTransferPerson(personIndex, targetAreaIndex),
          onUpdate: (patch) => onUpdatePerson(personIndex, patch),
        })
      )
    ),
    h(
      "div",
      { className: "person-add-row" },
      h(IconButton, {
        icon: "plus.png",
        hoverIcon: "plus_hover.png",
        label: "Agregar colaborador",
        onClick: onAddPerson,
      })
    )
  );
}
