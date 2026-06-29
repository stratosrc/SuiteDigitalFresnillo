import { useState } from "react";
import { downloadBlob } from "/static/js/shared/helpers.js";
import { Field, ToolFrame } from "/static/js/shared/layout.js";
import { h } from "/static/js/shared/react.js";

export default function Converter() {
  const [status, setStatus] = useState({ message: "Selecciona un archivo para convertir." });
  const submit = async (event) => {
    event.preventDefault();
    setStatus({ message: "Convirtiendo..." });
    try {
      const response = await fetch("/api/conversor/convertir", { method: "POST", body: new FormData(event.currentTarget) });
      await downloadBlob(response, "convertido.pdf");
      setStatus({ message: "PDF generado." });
    } catch (error) {
      setStatus({ message: error.message, error: true });
    }
  };
  return h(ToolFrame, {
    title: "Conversor a PDF",
    subtitle: "Conversión de archivos e imágenes a PDF",
    status,
    children: h("form", { className: "stack", onSubmit: submit }, h(Field, { label: "Archivo" }, h("input", { name: "source_file", type: "file", required: true })), h(Field, { label: "Páginas u hojas" }, h("input", { name: "selection", placeholder: "1, 2-4 o vacío para todo" })), h("button", null, "Convertir y descargar")),
    workspace: h("div", { className: "drop-illustration" }, h("img", { src: "/assets/convert.png", alt: "" }), h("strong", null, "Carga archivos desde el panel izquierdo"), h("span", null, "Imágenes, PDFs y documentos de Office compatibles con LibreOffice.")),
  });
}
