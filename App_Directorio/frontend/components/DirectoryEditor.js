import { h } from "/static/js/shared/react.js";
import { AreaSection } from "./AreaSection.js";

export function DirectoryEditor({
  directory,
  onAddArea,
  onAddPerson,
  onMoveArea,
  onMovePerson,
  onRemoveArea,
  onRemovePerson,
  onTransferPerson,
  onUpdateArea,
  onUpdateDirectory,
  onUpdatePerson,
}) {
  const areaOptions = directory.areas.map((area, index) => ({ index, name: area.name }));

  return h(
    "section",
    { className: "directory-workspace" },
    h(
      "div",
      { className: "directory-scroll" },
      h(
        "p",
        { className: "directory-instruction" },
        "Completa los datos generales y agrega las personas del directorio. Los campos se guardan automáticamente para recuperación."
      ),
      h(
        "div",
        { className: "directory-general-grid" },
        h(
          "label",
          null,
          h("span", null, "Unidad Administrativa"),
          h("input", {
            value: directory.title,
            placeholder: "Unidad administrativa, ej. Unidad de Transparencia",
            onChange: (event) => onUpdateDirectory({ title: event.target.value }),
          })
        ),
        h(
          "label",
          null,
          h("span", null, "Periodo"),
          h("input", {
            value: directory.period,
            placeholder: "ej. Enero - Marzo 2026",
            onChange: (event) => onUpdateDirectory({ period: event.target.value }),
          })
        )
      ),
      h(
        "div",
        { className: "area-list" },
        directory.areas.map((area, areaIndex) =>
          h(AreaSection, {
            key: area.localId || areaIndex,
            area,
            areaIndex,
            areaOptions,
            canMoveDown: areaIndex < directory.areas.length - 1,
            canMoveUp: areaIndex > 0,
            canRemove: directory.areas.length > 1,
            onAddPerson: () => onAddPerson(areaIndex),
            onAreaPositionCommit: (value) => onMoveArea(areaIndex, value - 1 - areaIndex),
            onMoveArea: (direction) => onMoveArea(areaIndex, direction),
            onMovePerson: (personIndex, direction) => onMovePerson(areaIndex, personIndex, direction),
            onRemoveArea: () => onRemoveArea(areaIndex),
            onRemovePerson: (personIndex) => onRemovePerson(areaIndex, personIndex),
            onTransferPerson: (personIndex, targetAreaIndex) => onTransferPerson(areaIndex, personIndex, targetAreaIndex),
            onUpdateArea: (patch) => onUpdateArea(areaIndex, patch),
            onUpdatePerson: (personIndex, patch) => onUpdatePerson(areaIndex, personIndex, patch),
          })
        )
      ),
      h("button", { type: "button", className: "add-area-button", onClick: onAddArea }, "+ Agregar Área")
    )
  );
}
