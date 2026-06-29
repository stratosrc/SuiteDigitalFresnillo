import { useState } from "react";
import { downloadBlob } from "../shared/helpers.js";
import { Field, ToolFrame } from "../shared/layout.js";
import { h } from "../shared/react.js";

export default function Directory() {
  const [title, setTitle] = useState("Directorio de Area");
  const [period, setPeriod] = useState("");
  const [areas, setAreas] = useState([{ name: "", personnel: [{ rank: "", name: "", position: "", email: "", start_date: "" }] }]);
  const [status, setStatus] = useState({ message: "" });

  const updateArea = (index, patch) => setAreas((items) => items.map((area, areaIndex) => (areaIndex === index ? { ...area, ...patch } : area)));
  const updatePerson = (areaIndex, personIndex, patch) =>
    setAreas((items) => items.map((area, index) => index === areaIndex ? { ...area, personnel: area.personnel.map((person, pIndex) => pIndex === personIndex ? { ...person, ...patch } : person) } : area));

  const submit = async (event) => {
    event.preventDefault();
    setStatus({ message: "Generando PDF..." });
    try {
      const response = await fetch("/api/directorio/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, period, areas }),
      });
      await downloadBlob(response, "directorio.pdf");
      setStatus({ message: "PDF generado." });
    } catch (error) {
      setStatus({ message: error.message, error: true });
    }
  };

  return h(ToolFrame, {
    title: "Directorio",
    subtitle: "Gestión y diseño del directorio de área",
    status,
    actions: h("button", { className: "compact-button", onClick: () => setAreas([...areas, { name: "", personnel: [{ rank: "", name: "", position: "", email: "", start_date: "" }] }]) }, "Agregar área"),
    children: [
      h(Field, { key: "title", label: "Titulo" }, h("input", { value: title, onChange: (event) => setTitle(event.target.value) })),
      h(Field, { key: "period", label: "Periodo" }, h("input", { value: period, onChange: (event) => setPeriod(event.target.value) })),
      h("button", { key: "submit", onClick: submit }, "Generar PDF"),
    ],
    workspace: h(
      "form",
      { className: "directory-sheet", onSubmit: submit },
      areas.map((area, areaIndex) =>
        h(
          "section",
          { key: areaIndex, className: "desktop-section" },
          h("div", { className: "section-title-row" }, h(Field, { label: "Área" }, h("input", { value: area.name, onChange: (event) => updateArea(areaIndex, { name: event.target.value }) })), h("button", { type: "button", className: "compact-button ghost", onClick: () => updateArea(areaIndex, { personnel: [...area.personnel, { rank: "", name: "", position: "", email: "", start_date: "" }] }) }, "Agregar persona")),
          area.personnel.map((person, personIndex) =>
            h(
              "div",
              { key: personIndex, className: "person-grid" },
              ["rank", "name", "position", "email", "start_date"].map((key) => h("input", { key, placeholder: { rank: "Rango/Clave/Nivel", name: "Nombre", position: "Cargo", email: "Correo", start_date: "Fecha de Alta" }[key], value: person[key], onChange: (event) => updatePerson(areaIndex, personIndex, { [key]: event.target.value }) })),
              h("button", { type: "button", className: "compact-button danger", onClick: () => updateArea(areaIndex, { personnel: area.personnel.filter((_, index) => index !== personIndex) }) }, "Quitar")
            )
          )
        )
      )
    ),
  });
}
