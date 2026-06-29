import { useEffect, useRef, useState } from "react";
import { downloadBlob } from "/static/js/shared/helpers.js";
import { Field, ToolFrame } from "/static/js/shared/layout.js";
import { h } from "/static/js/shared/react.js";

export default function Organization() {
  const [status, setStatus] = useState({ message: "Doble clic en el lienzo para agregar nodos rapido." });
  const [selected, setSelected] = useState([]);
  const [nodes, setNodes] = useState(() => ({
    a: { id: "a", name: "Direccion", role: "Titular", grid_x: 1, grid_y: 0, color: "#09519F" },
    b: { id: "b", name: "Coordinacion", role: "Responsable", grid_x: 1, grid_y: 1, color: "#3C8AC9" },
  }));
  const [connections, setConnections] = useState([{ id: "c", source_id: "a", target_id: "b", source_port: "bottom", target_port: "top", kind: "direct", manual_points: [] }]);
  const [meta, setMeta] = useState({ title: "Organigrama institucional", period: "", orientation: "horizontal", name: "", role: "", color: "#09519F" });
  const canvasRef = useRef(null);

  const draw = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = window.devicePixelRatio || 1;
    const box = canvas.getBoundingClientRect();
    canvas.width = Math.max(1000, box.width * dpr);
    canvas.height = Math.max(650, box.height * dpr);
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, box.width, box.height);
    const cellW = 250;
    const cellH = 170;
    const nodeW = 210;
    const nodeH = 92;
    connections.forEach((connection) => {
      const source = nodes[connection.source_id];
      const target = nodes[connection.target_id];
      if (!source || !target) return;
      const sx = source.grid_x * cellW + cellW / 2;
      const sy = source.grid_y * cellH + 120;
      const tx = target.grid_x * cellW + cellW / 2;
      const ty = target.grid_y * cellH + 28;
      const midY = (sy + ty) / 2;
      ctx.strokeStyle = "#09519F";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(sx, sy);
      ctx.lineTo(sx, midY);
      ctx.lineTo(tx, midY);
      ctx.lineTo(tx, ty);
      ctx.stroke();
      ctx.fillStyle = "#09519F";
      ctx.beginPath();
      ctx.moveTo(tx, ty);
      ctx.lineTo(tx - 6, ty - 10);
      ctx.lineTo(tx + 6, ty - 10);
      ctx.closePath();
      ctx.fill();
    });
    Object.values(nodes).forEach((node) => {
      const x = node.grid_x * cellW + (cellW - nodeW) / 2;
      const y = node.grid_y * cellH + 28;
      ctx.fillStyle = node.color;
      ctx.strokeStyle = selected.includes(node.id) ? "#22C55E" : node.color;
      ctx.lineWidth = selected.includes(node.id) ? 4 : 1;
      ctx.beginPath();
      ctx.roundRect(x, y, nodeW, nodeH, 6);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#ffffff";
      ctx.textAlign = "center";
      ctx.font = "700 14px Segoe UI, Arial";
      ctx.fillText(node.name || "ASIGNAR NOMBRE", x + nodeW / 2, y + 34);
      ctx.font = "12px Segoe UI, Arial";
      ctx.fillText(node.role || "", x + nodeW / 2, y + 62);
    });
  };

  useEffect(draw, [nodes, connections, selected]);
  useEffect(() => {
    window.addEventListener("resize", draw);
    return () => window.removeEventListener("resize", draw);
  });

  const hitNode = (event) => {
    const canvas = canvasRef.current;
    const box = canvas.getBoundingClientRect();
    const x = event.clientX - box.left;
    const y = event.clientY - box.top;
    return Object.values(nodes).find((node) => {
      const left = node.grid_x * 250 + 20;
      const top = node.grid_y * 170 + 28;
      return x >= left && x <= left + 210 && y >= top && y <= top + 92;
    });
  };

  const addNode = (gridX, gridY) => {
    const id = crypto.randomUUID ? crypto.randomUUID().replaceAll("-", "") : String(Date.now());
    setNodes({ ...nodes, [id]: { id, name: meta.name || "Nuevo nodo", role: meta.role || "Cargo", color: meta.color, grid_x: gridX ?? Object.keys(nodes).length + 1, grid_y: gridY ?? 1 } });
  };

  const exportPdf = async () => {
    try {
      const response = await fetch("/api/organigrama/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document: { title: meta.title, period: meta.period, page_orientation: meta.orientation, show_logos: true, nodes, connections, blocked_points: [] } }),
      });
      await downloadBlob(response, "organigrama.pdf");
      setStatus({ message: "PDF generado." });
    } catch (error) {
      setStatus({ message: error.message, error: true });
    }
  };

  return h(ToolFrame, {
    title: "Organigrama",
    subtitle: "Gestión del diseño y estructura institucional",
    status,
    actions: h("button", { className: "compact-button", onClick: exportPdf }, "Exportar PDF"),
    children: [
      h(Field, { key: "title", label: "Titulo" }, h("input", { value: meta.title, onChange: (event) => setMeta({ ...meta, title: event.target.value }) })),
      h(Field, { key: "period", label: "Periodo" }, h("input", { value: meta.period, onChange: (event) => setMeta({ ...meta, period: event.target.value }) })),
      h(Field, { key: "orientation", label: "Orientación" }, h("select", { value: meta.orientation, onChange: (event) => setMeta({ ...meta, orientation: event.target.value }) }, h("option", { value: "horizontal" }, "Horizontal"), h("option", { value: "vertical" }, "Vertical"))),
      h(Field, { key: "name", label: "Nombre" }, h("input", { value: meta.name, onChange: (event) => setMeta({ ...meta, name: event.target.value }) })),
      h(Field, { key: "role", label: "Cargo" }, h("input", { value: meta.role, onChange: (event) => setMeta({ ...meta, role: event.target.value }) })),
      h(Field, { key: "color", label: "Color" }, h("select", { value: meta.color, onChange: (event) => setMeta({ ...meta, color: event.target.value }) }, h("option", { value: "#09519F" }, "Azul institucional"), h("option", { value: "#3C8AC9" }, "Azul medio"), h("option", { value: "#9DC3E6" }, "Azul claro"), h("option", { value: "#797E85" }, "Gris institucional"))),
      h("div", { key: "buttons", className: "button-row" }, h("button", { onClick: () => addNode() }, "Agregar nodo"), h("button", { onClick: () => selected.length === 2 ? (setConnections([...connections, { id: String(Date.now()), source_id: selected[0], target_id: selected[1], source_port: "bottom", target_port: "top", kind: "direct", manual_points: [] }]), setSelected([])) : setStatus({ message: "Selecciona dos nodos con Shift + clic.", error: true }) }, "Conectar"), h("button", { className: "danger", onClick: () => { setNodes(Object.fromEntries(Object.entries(nodes).filter(([id]) => !selected.includes(id)))); setConnections(connections.filter((connection) => !selected.includes(connection.source_id) && !selected.includes(connection.target_id))); setSelected([]); } }, "Eliminar")),
    ],
    workspace: h("canvas", {
      ref: canvasRef,
      className: "org-canvas",
      onClick: (event) => {
        const node = hitNode(event);
        if (!node) return setSelected([]);
        setSelected(event.shiftKey ? [...new Set([...selected, node.id])].slice(-2) : [node.id]);
        setMeta({ ...meta, name: node.name, role: node.role, color: node.color });
      },
      onDoubleClick: (event) => {
        const box = canvasRef.current.getBoundingClientRect();
        addNode(Math.max(0, Math.round((event.clientX - box.left - 125) / 250)), Math.max(0, Math.round((event.clientY - box.top - 70) / 170)));
      },
    }),
  });
}
