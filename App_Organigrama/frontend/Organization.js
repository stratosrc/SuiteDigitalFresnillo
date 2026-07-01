import { useEffect, useRef, useState } from "react";
import { responseToBlob, saveBlob } from "/static/js/shared/helpers.js";
import { h } from "/static/js/shared/react.js";
import { loadHelp, loadPalette, postJson } from "./api.js";
import { HelpModal } from "./components/HelpModal.js";
import { HierarchyConfirmModal } from "./components/HierarchyConfirmModal.js";
import { NodeModal } from "./components/NodeModal.js";
import { BottomBar, CanvasStage, MetadataStrip, ToolStrip } from "./components/OrganizationLayout.js";
import { OrganizationMenu } from "./components/OrganizationMenu.js";
import { OrientationModal } from "./components/OrientationModal.js";
import { CELL_W, CELL_H, DEFAULT_PALETTE, NODE_HIERARCHY_RANK_BY_COLOR, NODE_LOGO_URL, PORTS, projectPayload, emptyDocument } from "./constants.js";
import { drawArrow, drawConnectionDraft, drawEmpty, drawGrid, drawNodeGhost } from "./utils/drawing.js";
import {
  distance,
  distanceToSegment,
  gridToWorld,
  nearestPort,
  nodeDistanceFromScreen,
  nodeAtCellId,
  nodeLayout,
  pointKey,
  portWorld,
  screenToWorld,
  worldToGrid,
} from "./utils/geometry.js";

export default function Organization() {
  const [document, setDocument] = useState(emptyDocument);
  const [routes, setRoutes] = useState([]);
  const [palette, setPalette] = useState(DEFAULT_PALETTE);
  const [help, setHelp] = useState(null);
  const [status, setStatus] = useState({ message: "Clic para crear nodo" });
  const [selected, setSelected] = useState({ type: null, id: null });
  const [fileMenuOpen, setFileMenuOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [nodeModal, setNodeModal] = useState(null);
  const [orientationModalOpen, setOrientationModalOpen] = useState(false);
  const [hierarchyConfirm, setHierarchyConfirm] = useState(null);
  const [viewport, setViewport] = useState({ x: 420, y: 250, zoom: 1 });
  const [hoverPort, setHoverPort] = useState(null);
  const [previewCell, setPreviewCell] = useState(null);
  const [connectionDraft, setConnectionDraft] = useState(null);
  const [manualPreview, setManualPreview] = useState(null);
  const [blockMode, setBlockMode] = useState(false);
  const [lastNodeId, setLastNodeId] = useState(null);
  const [nodeLogo, setNodeLogo] = useState(null);
  const [undoStack, setUndoStack] = useState([]);
  const [redoStack, setRedoStack] = useState([]);
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  const dragRef = useRef(null);

  useEffect(() => {
    loadPalette()
      .then((payload) => setPalette(payload.colors?.length ? payload.colors : DEFAULT_PALETTE))
      .catch(() => {});
    loadHelp()
      .then(setHelp)
      .catch(() => {});
    const image = new Image();
    image.onload = () => setNodeLogo(image);
    image.src = NODE_LOGO_URL;
  }, []);

  useEffect(() => {
    syncRoutes(document);
  }, [document]);

  useEffect(() => {
    draw();
  }, [document, routes, selected, viewport, hoverPort, previewCell, connectionDraft, manualPreview, blockMode, nodeLogo]);

  useEffect(() => {
    const onResize = () => draw();
    const onKeyDown = (event) => {
      if (nodeModal || helpOpen || orientationModalOpen || hierarchyConfirm) return;
      if ((event.key === "Delete" || event.key === "Backspace") && selected.id) {
        event.preventDefault();
        deleteSelection();
      }
      if (event.key === "Escape") {
        event.preventDefault();
        clearSelection();
      }
      if (event.ctrlKey && event.key.toLowerCase() === "z") {
        event.preventDefault();
        undo();
      }
      if (event.ctrlKey && (event.key.toLowerCase() === "y" || (event.shiftKey && event.key.toLowerCase() === "z"))) {
        event.preventDefault();
        redo();
      }
      if (event.ctrlKey && event.key.toLowerCase() === "n") {
        event.preventDefault();
        newProject();
      }
      if (event.ctrlKey && event.key.toLowerCase() === "o") {
        event.preventDefault();
        fileInputRef.current?.click();
      }
      if (event.ctrlKey && event.key.toLowerCase() === "s") {
        event.preventDefault();
        saveProject();
      }
    };
    window.addEventListener("resize", onResize);
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("resize", onResize);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [document, selected, nodeModal, helpOpen, orientationModalOpen, hierarchyConfirm, undoStack, redoStack]);

  const remember = () => {
    setUndoStack((items) => [...items.slice(-99), structuredClone(document)]);
    setRedoStack([]);
  };

  const applyDocument = (nextDocument, { rememberChange = true, message = "" } = {}) => {
    if (rememberChange) remember();
    setDocument(structuredClone(nextDocument));
    if (message) setStatus({ message });
  };

  const syncRoutes = async (nextDocument) => {
    try {
      const payload = await postJson("/api/organigrama/routes", { document: nextDocument });
      setRoutes(payload.routes || []);
    } catch {
      setRoutes([]);
    }
  };

  const normalizeDocument = async (nextDocument) => {
    const payload = await postJson("/api/organigrama/normalize", { document: nextDocument });
    setRoutes(payload.routes || []);
    return payload.document || nextDocument;
  };

  const addNodeWithPython = async ({ name, role, color, gridX, gridY }) => {
    try {
      const payload = await postJson("/api/organigrama/nodes", {
        document,
        name,
        role,
        color,
        grid_x: gridX,
        grid_y: gridY,
      });
      remember();
      setDocument(payload.document);
      setRoutes(payload.routes || []);
      const newest = Object.values(payload.document.nodes || {}).find((node) => node.grid_x === gridX && node.grid_y === gridY);
      setLastNodeId(newest?.id || null);
      setSelected({ type: "node", id: newest?.id || null });
      setStatus({ message: "Nodo agregado." });
    } catch (error) {
      if (error.status === 404) {
        addNodeLocally({ name, role, color, gridX, gridY });
        return;
      }
      setStatus({ message: error.message, error: true });
    }
  };

  const updateNodeWithPython = async ({ nodeId, name, role, color }) => {
    try {
      const payload = await postJson("/api/organigrama/nodes/update", {
        document,
        node_id: nodeId,
        name,
        role,
        color,
      });
      remember();
      setDocument(payload.document);
      setRoutes(payload.routes || []);
      setLastNodeId(nodeId);
      setSelected({ type: "node", id: nodeId });
      setStatus({ message: "Nodo actualizado." });
    } catch (error) {
      if (error.status === 404) {
        updateNodeLocally({ nodeId, name, role, color });
        return;
      }
      setStatus({ message: error.message, error: true });
    }
  };

  const addNodeLocally = ({ name, role, color, gridX, gridY }) => {
    if (nodeAtCellId(document, gridX, gridY)) {
      setStatus({ message: "La celda seleccionada ya contiene un nodo.", error: true });
      return;
    }
    const id = crypto.randomUUID ? crypto.randomUUID().replaceAll("-", "") : String(Date.now());
    applyDocument(
      {
        ...document,
        nodes: {
          ...document.nodes,
          [id]: { id, name, role, color, grid_x: gridX, grid_y: gridY },
        },
      },
      { message: "Nodo agregado." }
    );
    setLastNodeId(id);
    setSelected({ type: "node", id });
  };

  const updateNodeLocally = ({ nodeId, name, role, color }) => {
    if (!document.nodes[nodeId]) return;
    applyDocument(
      {
        ...document,
        nodes: {
          ...document.nodes,
          [nodeId]: { ...document.nodes[nodeId], name, role, color },
        },
      },
      { message: "Nodo actualizado." }
    );
    setLastNodeId(nodeId);
    setSelected({ type: "node", id: nodeId });
  };

  const addConnectionWithPython = async (source, target) => {
    try {
      const payload = await postJson("/api/organigrama/connections", {
        document,
        source_id: source.nodeId,
        target_id: target.nodeId,
        source_port: source.port,
        target_port: target.port,
      });
      remember();
      setDocument(payload.document);
      setRoutes(payload.routes || []);
      const connection = payload.document.connections.at(-1);
      setSelected({ type: "connection", id: connection?.id || null });
      setStatus({ message: "Conexion creada." });
    } catch (error) {
      setStatus({ message: error.message, error: true });
    }
  };

  const newProject = () => {
    applyDocument(emptyDocument(), { message: "Organigrama nuevo." });
    setSelected({ type: null, id: null });
    setLastNodeId(null);
  };

  const saveProject = async () => {
    const normalized = await normalizeDocument(document);
    const blob = new Blob([JSON.stringify(projectPayload(normalized), null, 2)], { type: "application/json" });
    const result = await saveBlob(blob, "organigrama.og", [
      { description: "Proyecto Organigrama", accept: { "application/json": [".og"] } },
    ]);
    setStatus({ message: result === "cancelled" ? "Guardado cancelado." : "Proyecto guardado." });
  };

  const loadProject = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const payload = JSON.parse(await file.text());
      const nextDocument = await normalizeDocument(payload.document || payload);
      applyDocument(nextDocument, { rememberChange: false, message: "Proyecto cargado." });
      setUndoStack([]);
      setRedoStack([]);
      setSelected({ type: null, id: null });
      setLastNodeId(Object.keys(nextDocument.nodes || {}).at(-1) || null);
    } catch (error) {
      setStatus({ message: `No se pudo cargar el proyecto: ${error.message}`, error: true });
    } finally {
      event.target.value = "";
    }
  };

  const exportPdf = async (orientation = document.page_orientation || "horizontal") => {
    try {
      const exportDocument = { ...document, page_orientation: orientation };
      const response = await fetch("/api/organigrama/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document: exportDocument }),
      });
      const blob = await responseToBlob(response);
      const result = await saveBlob(blob, "organigrama.pdf", [
        { description: "Archivo PDF", accept: { "application/pdf": [".pdf"] } },
      ]);
      setStatus({ message: result === "cancelled" ? "Exportacion cancelada." : "PDF generado." });
    } catch (error) {
      setStatus({ message: error.message, error: true });
    }
  };

  const deleteSelection = () => {
    if (!selected.id) return;
    const nextDocument = structuredClone(document);
    if (selected.type === "node") {
      delete nextDocument.nodes[selected.id];
      nextDocument.connections = nextDocument.connections.filter((item) => item.source_id !== selected.id && item.target_id !== selected.id);
    }
    if (selected.type === "connection") {
      nextDocument.connections = nextDocument.connections.filter((item) => item.id !== selected.id);
    }
    if (selected.type === "blocked") {
      nextDocument.blocked_points = (nextDocument.blocked_points || []).filter((point) => pointKey(point) !== selected.id);
    }
    applyDocument(nextDocument, { message: "Seleccion eliminada." });
    setSelected({ type: null, id: null });
  };

  const connectWithHierarchyCheck = (source, target) => {
    const sourceNode = document.nodes[source.nodeId];
    const targetNode = document.nodes[target.nodeId];
    if (!sourceNode || !targetNode) return;
    if (isInverseHierarchyConnection(sourceNode, targetNode)) {
      setHierarchyConfirm({
        source,
        target,
        sourceLabel: nodeFlowLabel(sourceNode),
        targetLabel: nodeFlowLabel(targetNode),
      });
      setStatus({ message: "Confirma la conexión jerárquica inversa." });
      return;
    }
    addConnectionWithPython(source, target);
  };

  const isInverseHierarchyConnection = (sourceNode, targetNode) => {
    const sourceRank = NODE_HIERARCHY_RANK_BY_COLOR[sourceNode.color];
    const targetRank = NODE_HIERARCHY_RANK_BY_COLOR[targetNode.color];
    return sourceRank != null && targetRank != null && sourceRank < targetRank;
  };

  const nodeFlowLabel = (node) => {
    const name = (node.name || "Sin nombre").split("\n").filter(Boolean).join(", ");
    return node.role ? `${name} — ${node.role}` : name;
  };

  const clearSelection = () => {
    setSelected({ type: null, id: null });
    setHoverPort(null);
    setManualPreview(null);
    setConnectionDraft(null);
    setStatus({ message: "Seleccion limpiada." });
  };

  const resetSelectedRoute = () => {
    if (selected.type !== "connection") return;
    const nextDocument = structuredClone(document);
    nextDocument.connections = nextDocument.connections.map((item) => (item.id === selected.id ? { ...item, manual_points: [] } : item));
    applyDocument(nextDocument, { message: "Ruta automatica restaurada." });
  };

  const undo = () => {
    setUndoStack((items) => {
      if (!items.length) return items;
      const previous = items[items.length - 1];
      setRedoStack((redoItems) => [...redoItems.slice(-99), structuredClone(document)]);
      setDocument(previous);
      setSelected({ type: null, id: null });
      return items.slice(0, -1);
    });
  };

  const redo = () => {
    setRedoStack((items) => {
      if (!items.length) return items;
      const next = items[items.length - 1];
      setUndoStack((undoItems) => [...undoItems.slice(-99), structuredClone(document)]);
      setDocument(next);
      setSelected({ type: null, id: null });
      return items.slice(0, -1);
    });
  };

  const focusNode = (nodeId = lastNodeId || Object.keys(document.nodes).at(-1)) => {
    const node = document.nodes[nodeId];
    const canvas = canvasRef.current;
    if (!node || !canvas) return;
    const box = canvas.getBoundingClientRect();
    const world = gridToWorld(node.grid_x, node.grid_y);
    setViewport((view) => ({
      ...view,
      x: box.width / 2 - world.x * view.zoom,
      y: box.height / 2 - world.y * view.zoom,
    }));
  };

  const panCamera = (dx, dy) => {
    setViewport((view) => ({ ...view, x: view.x + dx, y: view.y + dy }));
  };

  const zoomBy = (delta) => {
    const canvas = canvasRef.current;
    const box = canvas?.getBoundingClientRect();
    setViewport((view) => {
      const nextZoom = Math.min(3, Math.max(0.3, view.zoom + delta));
      if (!box) return { ...view, zoom: nextZoom };
      const center = { x: box.width / 2, y: box.height / 2 };
      const before = screenToWorld(center, view);
      return {
        zoom: nextZoom,
        x: center.x - before.x * nextZoom,
        y: center.y - before.y * nextZoom,
      };
    });
  };

  const draw = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = window.devicePixelRatio || 1;
    const box = canvas.getBoundingClientRect();
    canvas.width = Math.max(400, box.width * dpr);
    canvas.height = Math.max(300, box.height * dpr);
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, box.width, box.height);
    drawGrid(ctx, box, viewport);
    if (previewCell && !nodeAtCellId(document, previewCell.x, previewCell.y)) {
      drawNodeGhost(ctx, previewCell, viewport);
    }
    drawConnections(ctx);
    drawManualRouteGhost(ctx);
    if (connectionDraft) {
      const source = document.nodes[connectionDraft.source.nodeId];
      if (source) {
        const hoverTarget =
          hoverPort && hoverPort.nodeId !== connectionDraft.source.nodeId
            ? document.nodes[hoverPort.nodeId]
            : null;
        drawConnectionDraft(ctx, {
          start: worldToScreen(portWorld(source, connectionDraft.source.port)),
          end: hoverTarget ? worldToScreen(portWorld(hoverTarget, hoverPort.port)) : worldToScreen(connectionDraft.current),
          zoom: viewport.zoom,
        });
      }
    }
    drawBlockedPoints(ctx);
    Object.values(document.nodes).forEach((node) => drawNode(ctx, node));
    if (!Object.keys(document.nodes).length) drawEmpty(ctx, box);
  };

  const drawConnections = (ctx) => {
    const routeById = new Map(routes.map((route) => [route.connection_id, route]));
    document.connections.forEach((connection) => {
      const route = routeById.get(connection.id);
      const points = route?.points?.length ? route.points.map(([x, y]) => gridToWorld(x, y)) : fallbackConnectionPoints(connection);
      if (points.length < 2) return;
      const screenPoints = points.map(worldToScreen);
      ctx.strokeStyle = selected.type === "connection" && selected.id === connection.id ? "#22C55E" : "#09519F";
      ctx.lineWidth = selected.id === connection.id ? Math.max(3, 3 * viewport.zoom) : Math.max(2, 2.1 * viewport.zoom);
      ctx.lineCap = "butt";
      ctx.lineJoin = "miter";
      ctx.beginPath();
      screenPoints.forEach((point, index) => {
        if (index === 0) ctx.moveTo(point.x, point.y);
        else ctx.lineTo(point.x, point.y);
      });
      ctx.stroke();
      drawArrow(ctx, screenPoints, {
        length: Math.max(8, 12 * viewport.zoom),
        width: Math.max(8, 11 * viewport.zoom),
        targetGap: Math.max(7, 10 * viewport.zoom),
      });
    });
    drawConnectionHandles(ctx, routeById);
  };

  const drawConnectionHandles = (ctx, routeById) => {
    if (selected.type !== "connection") return;
    const connection = document.connections.find((item) => item.id === selected.id);
    const route = connection ? routeById.get(connection.id) : null;
    if (!route?.points?.length) return;
    const radius = Math.max(5, 6 * viewport.zoom);
    route.points.slice(1, -1).forEach(([gridX, gridY]) => {
      const screen = worldToScreen(gridToWorld(gridX, gridY));
      ctx.fillStyle = "#ffffff";
      ctx.strokeStyle = "#22C55E";
      ctx.lineWidth = Math.max(2, 2 * viewport.zoom);
      ctx.beginPath();
      ctx.arc(screen.x, screen.y, radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    });
  };

  const drawManualRouteGhost = (ctx) => {
    if (!manualPreview?.candidatePoints?.length) return;
    const screenPoints = manualPreview.candidatePoints.map(([gridX, gridY]) => worldToScreen(gridToWorld(gridX, gridY)));
    ctx.save();
    ctx.setLineDash([8, 5]);
    ctx.strokeStyle = manualPreview.collisionNodeIds?.length ? "#E11D48" : "#22C55E";
    ctx.lineWidth = Math.max(3, 3 * viewport.zoom);
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.beginPath();
    screenPoints.forEach((point, index) => {
      if (index === 0) ctx.moveTo(point.x, point.y);
      else ctx.lineTo(point.x, point.y);
    });
    ctx.stroke();
    ctx.restore();
  };

  const drawBlockedPoints = (ctx) => {
    (document.blocked_points || []).forEach((point) => {
      const center = worldToScreen(gridToWorld(point[0], point[1]));
      ctx.strokeStyle = selected.type === "blocked" && selected.id === pointKey(point) ? "#22C55E" : "#B72D2D";
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(center.x - 9, center.y - 9);
      ctx.lineTo(center.x + 9, center.y + 9);
      ctx.moveTo(center.x + 9, center.y - 9);
      ctx.lineTo(center.x - 9, center.y + 9);
      ctx.stroke();
    });
  };

  const drawNode = (ctx, node) => {
    const layout = nodeLayout(node, { includeLogo: document.show_logos });
    const topLeft = worldToScreen({ x: layout.left, y: layout.top });
    const width = layout.width * viewport.zoom;
    const height = layout.height * viewport.zoom;
    ctx.fillStyle = node.color;
    ctx.strokeStyle = selected.type === "node" && selected.id === node.id ? "#22C55E" : node.color;
    ctx.lineWidth = selected.type === "node" && selected.id === node.id ? 3 : 1;
    ctx.beginPath();
    ctx.roundRect(topLeft.x, topLeft.y, width, height, Math.max(0, 12 * viewport.zoom));
    ctx.fill();
    ctx.stroke();

    if (document.show_logos) drawNodeLogo(ctx, layout, node.color);

    ctx.fillStyle = "#ffffff";
    ctx.textBaseline = "top";
    layout.lines.forEach((line) => {
      const fontSize = Math.max(6, line.fontSize * viewport.zoom);
      ctx.font = `${line.isBold ? "700" : "400"} ${fontSize}px Segoe UI, Arial`;
      ctx.textAlign = line.align === "left" ? "left" : "center";
      const textX = line.align === "left" ? topLeft.x + layout.style.textPaddingX * viewport.zoom : topLeft.x + width / 2;
      const textY = topLeft.y + line.top * viewport.zoom;
      ctx.fillText(line.text, textX, textY, width - layout.style.textPaddingX * 2 * viewport.zoom);
      if (line.isUnderlined) {
        const metrics = ctx.measureText(line.text);
        const underlineY = textY + fontSize + Math.max(1, viewport.zoom);
        const underlineLeft = line.align === "left" ? textX : textX - metrics.width / 2;
        ctx.beginPath();
        ctx.moveTo(underlineLeft, underlineY);
        ctx.lineTo(underlineLeft + metrics.width, underlineY);
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = Math.max(1, viewport.zoom);
        ctx.stroke();
      }
    });

    if (hoverPort?.nodeId === node.id || selected.id === node.id) {
      PORTS.forEach((port) => {
        const point = portWorld(node, port);
        const screen = worldToScreen(point);
        const active = hoverPort?.nodeId === node.id && hoverPort?.port === port;
        const radius = Math.max(9, 12 * viewport.zoom);
        const glowRadius = radius + Math.max(5, 5 * viewport.zoom);
        ctx.globalAlpha = active ? 0.32 : 0.16;
        ctx.fillStyle = active ? "#22C55E" : "#4B57A0";
        ctx.beginPath();
        ctx.arc(screen.x, screen.y, glowRadius, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1;
        ctx.fillStyle = active ? "#22C55E" : "#4B57A0";
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = Math.max(3, 4 * viewport.zoom);
        ctx.beginPath();
        ctx.arc(screen.x, screen.y, radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        ctx.fillStyle = "#ffffff";
        ctx.beginPath();
        ctx.arc(screen.x, screen.y, Math.max(2, radius * 0.28), 0, Math.PI * 2);
        ctx.fill();
      });
    }
  };

  const drawNodeLogo = (ctx, layout, color) => {
    const center = worldToScreen({ x: layout.logoCenterX, y: layout.logoCenterY });
    const radius = layout.style.logoRadius * viewport.zoom;
    ctx.fillStyle = color;
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(center.x, center.y, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    if (!nodeLogo) return;
    const imageSize = layout.logoImageSize * viewport.zoom;
    ctx.drawImage(nodeLogo, center.x - imageSize / 2, center.y - imageSize / 2, imageSize, imageSize);
  };

  const canvasPoint = (event) => {
    const box = canvasRef.current.getBoundingClientRect();
    return { x: event.clientX - box.left, y: event.clientY - box.top };
  };

  const onMouseDown = (event) => {
    const screen = canvasPoint(event);
    const world = screenToWorld(screen, viewport);
    if (event.button === 2) {
      event.preventDefault();
      const node = hitNode(world);
      const connection = node ? null : hitConnection(screen);
      if (node) {
        dragRef.current = { type: "node", nodeId: node.id, startWorld: world, original: structuredClone(node), remembered: false };
        setSelected({ type: "node", id: node.id });
      } else if (connection) {
        dragRef.current = {
          type: "connection",
          connectionId: connection.id,
          startWorld: world,
          originalPoints: getConnectionManualPoints(connection),
          remembered: false,
        };
        setSelected({ type: "connection", id: connection.id });
      } else {
        clearSelection();
        dragRef.current = { type: "pan", startScreen: screen, original: { ...viewport } };
      }
      return;
    }
    if (event.button !== 0) return;
    const manualEdit = hitSelectedRouteEditor(screen);
    if (manualEdit) {
      dragRef.current = { type: "manual-route", ...manualEdit };
      setManualPreview(null);
      return;
    }
    const port = hitPort(screen) || nearestNodePort(screen);
    if (port) {
      setHoverPort(port);
      setConnectionDraft({ source: port, current: world });
      dragRef.current = { type: "connect" };
      return;
    }
    const node = hitNode(world);
    if (node) {
      setSelected({ type: "node", id: node.id });
      return;
    }
    const connection = hitConnection(screen);
    if (connection) {
      setSelected({ type: "connection", id: connection.id });
      return;
    }
    const blocked = hitBlockedPoint(screen);
    if (blocked) {
      setSelected({ type: "blocked", id: pointKey(blocked) });
      return;
    }
    const cell = worldToGrid(world);
    if (blockMode) {
      toggleBlockedPoint(cell);
      return;
    }
    setSelected({ type: null, id: null });
    setNodeModal({ mode: "create", gridX: cell.x, gridY: cell.y, name: "", role: "", color: palette[0]?.value || "#09519F" });
  };

  const onMouseMove = (event) => {
    const screen = canvasPoint(event);
    const world = screenToWorld(screen, viewport);
    const drag = dragRef.current;
    if (drag?.type === "pan") {
      setViewport({ ...drag.original, x: drag.original.x + screen.x - drag.startScreen.x, y: drag.original.y + screen.y - drag.startScreen.y });
      return;
    }
    if (drag?.type === "node") {
      const nextCell = worldToGrid(world);
      const occupantId = nodeAtCellId(document, nextCell.x, nextCell.y);
      if (occupantId && occupantId !== drag.nodeId) {
        setStatus({ message: "La celda seleccionada ya contiene un nodo.", error: true });
        return;
      }
      if (!drag.remembered) {
        remember();
        drag.remembered = true;
      }
      setDocument((current) => ({
        ...current,
        nodes: {
          ...current.nodes,
          [drag.nodeId]: { ...current.nodes[drag.nodeId], grid_x: nextCell.x, grid_y: nextCell.y },
        },
      }));
      return;
    }
    if (drag?.type === "connection") {
      const deltaGrid = { x: (world.x - drag.startWorld.x) / CELL_W, y: (world.y - drag.startWorld.y) / CELL_H };
      if (!drag.remembered) {
        remember();
        drag.remembered = true;
      }
      setDocument((current) => ({
        ...current,
        connections: current.connections.map((connection) =>
          connection.id === drag.connectionId
            ? {
                ...connection,
                manual_points: drag.originalPoints.map((point) => [point[0] + deltaGrid.x, point[1] + deltaGrid.y]),
              }
            : connection
        ),
      }));
      return;
    }
    if (drag?.type === "connect") {
      setHoverPort(nearestNodePort(screen, connectionDraft?.source?.nodeId));
      setConnectionDraft((draft) => (draft ? { ...draft, current: world } : draft));
      return;
    }
    if (drag?.type === "manual-route") {
      previewManualRoute(drag, world, false);
      return;
    }
    const port = hitPort(screen) || nearestNodePort(screen);
    const node = hitNode(world);
    const connection = node || port ? null : hitConnection(screen);
    const blocked = node || port || connection ? null : hitBlockedPoint(screen);
    const cell = worldToGrid(world);
    setHoverPort(port);
    setPreviewCell(!blockMode && !port && !node && !connection && !blocked && !nodeAtCellId(document, cell.x, cell.y) ? cell : null);
  };

  const onMouseUp = (event) => {
    const screen = canvasPoint(event);
    if (dragRef.current?.type === "connect" && connectionDraft) {
      const target = hitPort(screen) || nearestNodePort(screen, connectionDraft.source.nodeId);
      if (target && target.nodeId !== connectionDraft.source.nodeId) {
        connectWithHierarchyCheck(connectionDraft.source, target);
      }
      setConnectionDraft(null);
      setHoverPort(null);
    }
    if (dragRef.current?.type === "manual-route") {
      previewManualRoute(dragRef.current, screenToWorld(screen, viewport), true);
    }
    dragRef.current = null;
  };

  const hitNode = (world) => {
    return Object.values(document.nodes).find((node) => {
      const layout = nodeLayout(node);
      return world.x >= layout.left && world.x <= layout.right && world.y >= layout.top && world.y <= layout.bottom;
    });
  };

  const hitPort = (screen) => {
    const radius = Math.max(16, 18 * viewport.zoom);
    for (const node of Object.values(document.nodes)) {
      for (const port of PORTS) {
        const point = worldToScreen(portWorld(node, port));
        if (distance(screen, point) <= radius) return { nodeId: node.id, port };
      }
    }
    return null;
  };

  const nearestNodePort = (screen, excludedNodeId = null) => {
    const maxDistance = Math.max(18, 34 * viewport.zoom);
    let closest = null;
    let closestDistance = maxDistance;
    Object.values(document.nodes).forEach((node) => {
      if (node.id === excludedNodeId) return;
      const currentDistance = nodeDistanceFromScreen(node, screen, viewport);
      if (currentDistance <= closestDistance) {
        closestDistance = currentDistance;
        closest = { nodeId: node.id, port: nearestPort(node, screen, viewport) };
      }
    });
    return closest;
  };

  const hitConnection = (screen) => {
    const routeById = new Map(routes.map((route) => [route.connection_id, route]));
    return document.connections.find((connection) => {
      const route = routeById.get(connection.id);
      const points = route?.points?.length ? route.points.map(([x, y]) => worldToScreen(gridToWorld(x, y))) : fallbackConnectionPoints(connection).map(worldToScreen);
      return points.some((point, index) => index > 0 && distanceToSegment(screen, points[index - 1], point) < 8);
    });
  };

  const hitSelectedRouteEditor = (screen) => {
    if (selected.type !== "connection") return null;
    const route = routes.find((item) => item.connection_id === selected.id);
    if (!route?.points?.length) return null;
    const bendIndex = hitBendPoint(route, screen);
    if (bendIndex !== null) return { connectionId: selected.id, kind: "bend", index: bendIndex };
    const segmentIndex = hitMovableSegment(route, screen);
    if (segmentIndex !== null) return { connectionId: selected.id, kind: "segment", index: segmentIndex };
    return null;
  };

  const hitBendPoint = (route, screen) => {
    let bestIndex = null;
    let bestDistance = Math.max(9, 10 * viewport.zoom);
    route.points.slice(1, -1).forEach(([gridX, gridY], offset) => {
      const point = worldToScreen(gridToWorld(gridX, gridY));
      const currentDistance = distance(screen, point);
      if (currentDistance <= bestDistance) {
        bestDistance = currentDistance;
        bestIndex = offset + 1;
      }
    });
    return bestIndex;
  };

  const hitMovableSegment = (route, screen) => {
    if (route.points.length < 4) return null;
    let bestIndex = null;
    let bestDistance = Math.max(10, 12 * viewport.zoom);
    for (let index = 1; index <= route.points.length - 3; index += 1) {
      const start = worldToScreen(gridToWorld(route.points[index][0], route.points[index][1]));
      const end = worldToScreen(gridToWorld(route.points[index + 1][0], route.points[index + 1][1]));
      const currentDistance = distanceToSegment(screen, start, end);
      if (currentDistance < bestDistance) {
        bestDistance = currentDistance;
        bestIndex = index;
      }
    }
    return bestIndex;
  };

  const previewManualRoute = async (drag, world, commit) => {
    try {
      const payload = await postJson("/api/organigrama/connections/manual-route", {
        document,
        connection_id: drag.connectionId,
        kind: drag.kind,
        index: drag.index,
        pointer: [world.x / CELL_W, world.y / CELL_H],
        commit,
      });
      setManualPreview({
        candidatePoints: payload.candidate_points || [],
        collisionNodeIds: payload.collision_node_ids || [],
      });
      if (commit) {
        if (payload.collision_node_ids?.length) {
          setStatus({ message: "Posicion no valida: la ruta atraviesa nodos.", error: true });
        } else {
          remember();
          setDocument(payload.document);
          setRoutes(payload.routes || []);
          setStatus({ message: "Ruta manual guardada." });
        }
        setManualPreview(null);
      }
    } catch (error) {
      setStatus({ message: error.message, error: true });
      if (commit) setManualPreview(null);
    }
  };

  const hitBlockedPoint = (screen) => {
    return (document.blocked_points || []).find((point) => distance(screen, worldToScreen(gridToWorld(point[0], point[1]))) <= 12);
  };

  const toggleBlockedPoint = (cell) => {
    remember();
    const key = pointKey([cell.x, cell.y]);
    const exists = (document.blocked_points || []).some((point) => pointKey(point) === key);
    setDocument({
      ...document,
      blocked_points: exists
        ? (document.blocked_points || []).filter((point) => pointKey(point) !== key)
        : [...(document.blocked_points || []), [cell.x, cell.y]],
    });
    setSelected(exists ? { type: null, id: null } : { type: "blocked", id: key });
  };

  const getConnectionManualPoints = (connection) => {
    if (connection.manual_points?.length) return connection.manual_points.map((point) => [Number(point[0]), Number(point[1])]);
    const route = routes.find((item) => item.connection_id === connection.id);
    const points = route?.points || [];
    return points.slice(1, -1).map((point) => [Number(point[0]), Number(point[1])]);
  };

  const worldToScreen = (point) => ({ x: point.x * viewport.zoom + viewport.x, y: point.y * viewport.zoom + viewport.y });
  const fallbackConnectionPoints = (connection) => {
    const source = document.nodes[connection.source_id];
    const target = document.nodes[connection.target_id];
    if (!source || !target) return [];
    const start = portWorld(source, connection.source_port || "bottom");
    const end = portWorld(target, connection.target_port || "top");
    const midY = (start.y + end.y) / 2;
    return [start, { x: start.x, y: midY }, { x: end.x, y: midY }, end];
  };

  return h(
    "main",
    { className: "org-desktop" },
    h(OrganizationMenu, {
      fileMenuOpen,
      setFileMenuOpen,
      onNew: newProject,
      onSaveProject: saveProject,
      onLoadProject: () => fileInputRef.current?.click(),
      onExportPdf: () => setOrientationModalOpen(true),
      onHelp: () => setHelpOpen(true),
    }),
    h("input", { ref: fileInputRef, className: "org-hidden-input", type: "file", accept: ".og,application/json", onChange: loadProject }),
    h(MetadataStrip, { document, setDocument }),
    h(ToolStrip, { document, setDocument, selected, deleteSelection, resetSelectedRoute, panCamera }),
    h(CanvasStage, {
      canvasRef,
      onMouseDown,
      onMouseMove,
      onMouseUp,
      onMouseLeave: () => (setHoverPort(null), setPreviewCell(null)),
      onDoubleClick: (event) => {
        const node = hitNode(screenToWorld(canvasPoint(event), viewport));
        if (node) setNodeModal({ mode: "edit", nodeId: node.id, name: node.name, role: node.role, color: node.color });
      },
      onWheel: (event) => {
        if (!event.ctrlKey) return;
        event.preventDefault();
        zoomBy(event.deltaY > 0 ? -0.1 : 0.1);
      },
    }),
    h(BottomBar, { focusNode, undo, redo, undoStack, redoStack, status, viewport, zoomBy }),
    nodeModal ? h(NodeModal, { modal: nodeModal, palette, onSave: nodeModal.mode === "edit" ? updateNodeWithPython : addNodeWithPython, onClose: () => setNodeModal(null) }) : null,
    orientationModalOpen
      ? h(OrientationModal, {
          current: document.page_orientation || "horizontal",
          onSelect: (orientation) => {
            setOrientationModalOpen(false);
            setDocument({ ...document, page_orientation: orientation });
            exportPdf(orientation);
          },
          onClose: () => setOrientationModalOpen(false),
        })
      : null,
    hierarchyConfirm
      ? h(HierarchyConfirmModal, {
          sourceLabel: hierarchyConfirm.sourceLabel,
          targetLabel: hierarchyConfirm.targetLabel,
          onConfirm: () => {
            const pending = hierarchyConfirm;
            setHierarchyConfirm(null);
            addConnectionWithPython(pending.source, pending.target);
          },
          onCancel: () => {
            setHierarchyConfirm(null);
            setStatus({ message: "Conexión cancelada." });
          },
        })
      : null,
    helpOpen ? h(HelpModal, { content: help, onClose: () => setHelpOpen(false) }) : null
  );
}

