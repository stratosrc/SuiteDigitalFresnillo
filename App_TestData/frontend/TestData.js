import { useEffect, useRef, useState } from "react";
import { cloneRectangles, downloadBlob, fileToDataUrl, navigate, normalizeRect } from "/static/js/shared/helpers.js";
import { Modal } from "/static/js/shared/layout.js";
import { h } from "/static/js/shared/react.js";

const emptyHistory = () => ({ reserved: [], confidential: [], other_law: [] });

const defaultRedactionForm = () => ({
  concept_id: "1",
  classification: "general",
  legal_basis: "",
  reason: "",
  rows: "1",
  paragraphs: "1",
  object: "",
  articles: "",
  law: "",
});

export default function TestData() {
  const [status, setStatus] = useState({
    message: "Sin PDF cargado. Usa Nuevo (Ctrl+N) para elegir un documento o abre un proyecto con Ctrl+O.",
  });
  const [concepts, setConcepts] = useState([]);
  const [catalogueSections, setCatalogueSections] = useState([]);
  const [helpContent, setHelpContent] = useState(null);
  const [session, setSession] = useState(null);
  const [page, setPage] = useState(1);
  const [zoom, setZoom] = useState(100);
  const [rectangles, setRectangles] = useState([]);
  const [selectedRectId, setSelectedRectId] = useState(null);
  const [undoStack, setUndoStack] = useState([]);
  const [redoStack, setRedoStack] = useState([]);
  const [sourcePdfData, setSourcePdfData] = useState("");
  const [sourcePdfName, setSourcePdfName] = useState("");
  const [classificationHistory, setClassificationHistory] = useState(emptyHistory);
  const [form, setForm] = useState(defaultRedactionForm);
  const [fileMenuOpen, setFileMenuOpen] = useState(false);
  const [activeModal, setActiveModal] = useState(null);
  const [pendingRect, setPendingRect] = useState(null);
  const [editingRectId, setEditingRectId] = useState(null);
  const fileInputRef = useRef(null);
  const projectInputRef = useRef(null);
  const canvasRef = useRef(null);
  const imageRef = useRef(null);
  const drawingRef = useRef(null);
  const interactionRef = useRef(null);
  const scaleRef = useRef(1);

  useEffect(() => {
    fetch("/api/catalogo")
      .then((response) => response.json())
      .then((payload) => {
        setConcepts(payload.items || []);
        setCatalogueSections(payload.sections || []);
      })
      .catch(() => setConcepts([{ id: 1, name: "Nombre" }]));
    fetch("/api/testdata/help")
      .then((response) => response.json())
      .then((payload) => setHelpContent(payload))
      .catch(() => setHelpContent(null));
  }, []);

  const rememberRectangles = () => {
    setUndoStack((items) => [...items.slice(-19), cloneRectangles(rectangles)]);
    setRedoStack([]);
  };

  const replaceRectangles = (nextRectangles, remember = true) => {
    if (remember) {
      setUndoStack((items) => [...items.slice(-19), cloneRectangles(rectangles)]);
      setRedoStack([]);
    }
    setRectangles(cloneRectangles(nextRectangles));
  };

  const undo = () => {
    setUndoStack((items) => {
      if (!items.length) return items;
      const previous = items[items.length - 1];
      setRedoStack((redoItems) => [...redoItems.slice(-19), cloneRectangles(rectangles)]);
      setRectangles(cloneRectangles(previous));
      setSelectedRectId(null);
      return items.slice(0, -1);
    });
  };

  const redo = () => {
    setRedoStack((items) => {
      if (!items.length) return items;
      const next = items[items.length - 1];
      setUndoStack((undoItems) => [...undoItems.slice(-19), cloneRectangles(rectangles)]);
      setRectangles(cloneRectangles(next));
      setSelectedRectId(null);
      return items.slice(0, -1);
    });
  };

  const normalizeRectangles = async (items) => {
    const response = await fetch("/api/testdata/rectangles/normalize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: session?.session_id || "draft", rectangles: items }),
    });
    if (!response.ok) return cloneRectangles(items);
    const payload = await response.json();
    return payload.rectangles || cloneRectangles(items);
  };

  const deleteSelectedRectangle = async () => {
    if (!selectedRectId) return;
    const response = await fetch("/api/testdata/rectangles/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: session?.session_id || "draft",
        rectangles,
        selected_rect_id: selectedRectId,
      }),
    });
    if (!response.ok) return;
    const payload = await response.json();
    replaceRectangles(payload.rectangles || []);
    setSelectedRectId(null);
  };

  const canvasRect = (rect) => {
    const scale = scaleRef.current;
    return {
      x: rect.x1 * scale,
      y: rect.y1 * scale,
      width: (rect.x2 - rect.x1) * scale,
      height: (rect.y2 - rect.y1) * scale,
    };
  };

  const rectHandles = (rect) => {
    const box = canvasRect(rect);
    const size = 8;
    return [
      { name: "nw", x: box.x, y: box.y },
      { name: "ne", x: box.x + box.width, y: box.y },
      { name: "sw", x: box.x, y: box.y + box.height },
      { name: "se", x: box.x + box.width, y: box.y + box.height },
    ].map((handle) => ({ ...handle, left: handle.x - size / 2, top: handle.y - size / 2, size }));
  };

  const draw = (rectanglesToDraw = rectangles, pageToDraw = page) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (imageRef.current) ctx.drawImage(imageRef.current, 0, 0);
    ctx.lineWidth = 2;
    ctx.font = "13px Segoe UI, Arial";
    rectanglesToDraw.filter((rect) => rect.page === pageToDraw - 1).forEach((rect, index) => {
      const scale = scaleRef.current;
      const x = rect.x1 * scale;
      const y = rect.y1 * scale;
      const w = (rect.x2 - rect.x1) * scale;
      const hh = (rect.y2 - rect.y1) * scale;
      ctx.fillStyle = "rgba(255,255,255,0.72)";
      ctx.strokeStyle = rect.id === selectedRectId ? "#22C55E" : "#263238";
      ctx.lineWidth = rect.id === selectedRectId ? 3 : 2;
      ctx.fillRect(x, y, w, hh);
      ctx.strokeRect(x, y, w, hh);
      ctx.fillStyle = "#263238";
      ctx.fillText(rect.label || `#${index + 1}`, x + 5, y + 17);
      if (rect.id === selectedRectId) {
        ctx.fillStyle = "#22C55E";
        rectHandles(rect).forEach((handle) => ctx.fillRect(handle.left, handle.top, handle.size, handle.size));
      }
    });
    if (drawingRef.current) {
      const rect = drawingRef.current;
      ctx.strokeStyle = "#22C55E";
      ctx.setLineDash([6, 4]);
      ctx.strokeRect(Math.min(rect.x1, rect.x2), Math.min(rect.y1, rect.y2), Math.abs(rect.x2 - rect.x1), Math.abs(rect.y2 - rect.y1));
      ctx.setLineDash([]);
    }
  };

  useEffect(draw, [rectangles, page, selectedRectId]);

  useEffect(() => {
    const onKeyDown = (event) => {
      if (activeModal) return;
      if ((event.key === "Delete" || event.key === "Backspace") && selectedRectId) {
        event.preventDefault();
        deleteSelectedRectangle();
      }
      if (event.ctrlKey && event.key.toLowerCase() === "z") {
        event.preventDefault();
        undo();
      }
      if (event.ctrlKey && (event.key.toLowerCase() === "y" || (event.shiftKey && event.key.toLowerCase() === "z"))) {
        event.preventDefault();
        redo();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [activeModal, selectedRectId, rectangles]);

  const loadPage = (nextPage, currentSession = session, rectanglesToDraw = rectangles) => {
    if (!currentSession) return;
    const img = new Image();
    img.onload = () => {
      imageRef.current = img;
      const canvas = canvasRef.current;
      canvas.width = img.width;
      canvas.height = img.height;
      scaleRef.current = img.width / currentSession.width;
      draw(rectanglesToDraw, nextPage);
    };
    img.src = `/api/testdata/${currentSession.session_id}/page/${nextPage}.png?ts=${Date.now()}`;
  };

  const upload = async (event) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const sourceFile = data.get("pdf");
    setStatus({ message: "Cargando PDF..." });
    const response = await fetch("/api/testdata/upload", { method: "POST", body: data });
    if (!response.ok) {
      setStatus({ message: (await response.json()).detail || "No se pudo cargar.", error: true });
      return;
    }
    const payload = await response.json();
    if (sourceFile instanceof File) {
      setSourcePdfData(await fileToDataUrl(sourceFile));
      setSourcePdfName(sourceFile.name);
    }
    setSession(payload);
    setRectangles([]);
    setSelectedRectId(null);
    setUndoStack([]);
    setRedoStack([]);
    setClassificationHistory(emptyHistory());
    setPage(1);
    setZoom(100);
    loadPage(1, payload, []);
    setStatus({ message: "PDF cargado. Arrastra sobre el documento para marcar testados." });
  };

  const startNewProject = () => {
    setSession(null);
    setRectangles([]);
    setSelectedRectId(null);
    setUndoStack([]);
    setRedoStack([]);
    setClassificationHistory(emptyHistory());
    setSourcePdfData("");
    setSourcePdfName("");
    setPage(1);
    setZoom(100);
    imageRef.current = null;
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
    fileInputRef.current?.click();
  };

  const pointer = (event) => {
    const box = canvasRef.current.getBoundingClientRect();
    const canvas = canvasRef.current;
    return {
      x: (event.clientX - box.left) * (canvas.width / box.width),
      y: (event.clientY - box.top) * (canvas.height / box.height),
    };
  };

  const hitTestRectangle = (point) => {
    const pageRectangles = rectangles.filter((rect) => rect.page === page - 1);
    for (let index = pageRectangles.length - 1; index >= 0; index -= 1) {
      const rect = pageRectangles[index];
      const handle = rectHandles(rect).find((item) => point.x >= item.left && point.x <= item.left + item.size && point.y >= item.top && point.y <= item.top + item.size);
      if (handle) return { rect, mode: "resize", handle: handle.name };
      const box = canvasRect(rect);
      if (point.x >= box.x && point.x <= box.x + box.width && point.y >= box.y && point.y <= box.y + box.height) {
        return { rect, mode: "move" };
      }
    }
    return null;
  };

  const finishRectangle = () => {
    const draft = drawingRef.current;
    drawingRef.current = null;
    if (!draft || !session) return draw();
    const scale = scaleRef.current;
    const left = Math.min(draft.x1, draft.x2) / scale;
    const top = Math.min(draft.y1, draft.y2) / scale;
    const right = Math.max(draft.x1, draft.x2) / scale;
    const bottom = Math.max(draft.y1, draft.y2) / scale;
    if (right - left < 4 || bottom - top < 4) return draw();
    setPendingRect({
      page: page - 1,
      x1: Math.max(0, left),
      y1: Math.max(0, top),
      x2: Math.min(session.width, right),
      y2: Math.min(session.height, bottom),
    });
    setEditingRectId(null);
    setActiveModal("redaction");
  };

  const openRectangleEditor = (rect) => {
    setSelectedRectId(rect.id);
    setPendingRect(null);
    setEditingRectId(rect.id);
    setForm({
      concept_id: String(rect.concept_id || 1),
      classification: rect.classification || "general",
      legal_basis: rect.legal_basis || "",
      reason: rect.reason || "",
      rows: String(rect.rows || 1),
      paragraphs: String(rect.paragraphs || 1),
      object: rect.object || "",
      articles: rect.articles || "",
      law: rect.law || "",
    });
    setActiveModal("redaction");
  };

  const acceptPendingRedaction = async () => {
    const concept = concepts.find((item) => String(item.id) === String(form.concept_id));
    const redactionData = {
      classification: form.classification,
      concept_id: Number(form.concept_id || 1),
      concept_name: concept?.name || "",
      legal_basis: form.legal_basis,
      reason: form.reason,
      rows: Number(form.rows) || 1,
      paragraphs: Number(form.paragraphs) || 1,
      object: form.object,
      articles: form.articles,
      law: form.law,
    };

    let nextRectangles = rectangles;
    let selectedId = editingRectId;
    if (editingRectId) {
      nextRectangles = rectangles.map((rect) => (rect.id === editingRectId ? { ...rect, ...redactionData } : rect));
    } else if (pendingRect) {
      selectedId = crypto.randomUUID ? crypto.randomUUID() : `rect-${Date.now()}`;
      nextRectangles = [...rectangles, { ...pendingRect, id: selectedId, ...redactionData }];
    } else {
      return;
    }
    replaceRectangles(await normalizeRectangles(nextRectangles));

    if (["reserved", "confidential", "other_law"].includes(form.classification)) {
      const historyEntry =
        form.classification === "other_law"
          ? { object: form.object, articles: form.articles, law: form.law, rows: form.rows, paragraphs: form.paragraphs }
          : { legal_basis: form.legal_basis, reason: form.reason, rows: form.rows, paragraphs: form.paragraphs };
      setClassificationHistory((history) => ({
        ...history,
        [form.classification]: [historyEntry, ...history[form.classification]].slice(0, 20),
      }));
    }
    setSelectedRectId(selectedId);
    setPendingRect(null);
    setEditingRectId(null);
    setActiveModal(null);
  };

  const exportPdf = async () => {
    if (!session) return;
    setStatus({ message: "Exportando PDF..." });
    try {
      const response = await fetch("/api/testdata/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: session.session_id, rectangles }),
      });
      await downloadBlob(response, "testado.pdf");
      setStatus({ message: "PDF testado generado." });
    } catch (error) {
      setStatus({ message: error.message, error: true });
    }
  };

  const goToPage = (nextPage) => {
    if (!session || nextPage < 1 || nextPage > session.page_count) return;
    setPage(nextPage);
    loadPage(nextPage);
  };

  const saveProject = () => {
    const payload = {
      app: "testdata-web",
      schema_version: 1,
      page,
      zoom,
      rectangles,
      histories: classificationHistory,
      pdf_name: sourcePdfName,
      pdf_data: sourcePdfData,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "testdata-web.tdweb";
    link.click();
    URL.revokeObjectURL(url);
  };

  const loadProject = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const payload = JSON.parse(await file.text());
      const nextRectangles = await normalizeRectangles(Array.isArray(payload.rectangles) ? payload.rectangles : []);
      const nextPage = Number(payload.page) || 1;
      const nextZoom = Number(payload.zoom) || 100;
      setUndoStack([]);
      setRedoStack([]);
      setSelectedRectId(null);
      setRectangles(nextRectangles);
      setPage(nextPage);
      setZoom(nextZoom);
      setClassificationHistory(payload.histories || emptyHistory());
      setSourcePdfData(payload.pdf_data || "");
      setSourcePdfName(payload.pdf_name || "");
      if (payload.pdf_data) {
        const response = await fetch("/api/testdata/upload-base64", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ filename: payload.pdf_name || "proyecto.pdf", data: payload.pdf_data }),
        });
        if (!response.ok) throw new Error((await response.json()).detail || "No se pudo restaurar el PDF del proyecto.");
        const restoredSession = await response.json();
        setSession(restoredSession);
        loadPage(nextPage, restoredSession, nextRectangles);
        setStatus({ message: "Proyecto cargado con su PDF." });
      } else {
        setSession(null);
        imageRef.current = null;
        const canvas = canvasRef.current;
        if (canvas) canvas.getContext("2d").clearRect(0, 0, canvas.width, canvas.height);
        setStatus({ message: "Proyecto cargado sin PDF embebido. Carga el PDF original para renderizar y exportar." });
      }
    } catch (error) {
      setStatus({ message: `No se pudo cargar el proyecto: ${error.message}`, error: true });
    } finally {
      event.target.value = "";
    }
  };

  return h(
    "main",
    { className: "testdata-desktop" },
    h(
      "section",
      { className: "testdata-menu" },
      h(
        "div",
        { className: "file-menu-wrap" },
        h("button", { onClick: () => setFileMenuOpen(!fileMenuOpen) }, "Archivo"),
        fileMenuOpen
          ? h(
              "div",
              { className: "file-dropdown" },
              h("button", { onClick: () => (setFileMenuOpen(false), startNewProject()) }, "Nuevo"),
              h("button", { onClick: () => (setFileMenuOpen(false), projectInputRef.current?.click()) }, "Cargar proyecto"),
              h("button", { onClick: () => (setFileMenuOpen(false), saveProject()) }, "Guardar proyecto"),
              h("button", { onClick: () => (setFileMenuOpen(false), exportPdf()) }, "Exportar PDF")
            )
          : null
      ),
      h("button", { onClick: () => setActiveModal("catalogue") }, "Catálogo"),
      h("button", { onClick: () => setActiveModal("help") }, "Ayuda"),
      h("button", { className: "exit-button", onClick: () => navigate("/") }, "Salir")
    ),
    h(
      "form",
      { className: "hidden-upload", onSubmit: upload },
      h("input", {
        ref: fileInputRef,
        name: "pdf",
        type: "file",
        accept: "application/pdf",
        onChange: (event) => event.currentTarget.form?.requestSubmit(),
      })
    ),
    h("input", { ref: projectInputRef, className: "hidden-upload", type: "file", accept: ".tdweb,application/json", onChange: loadProject }),
    h(
      "section",
      { className: "testdata-toolbar" },
      h("button", { className: "icon-button", title: "Deshacer", onClick: undo, disabled: undoStack.length === 0 }, h("img", { src: "/testdata-assets/undo.png", alt: "" })),
      h("button", { className: "icon-button", title: "Rehacer", onClick: redo, disabled: redoStack.length === 0 }, h("img", { src: "/testdata-assets/redo.png", alt: "" })),
      h("button", { className: "icon-button danger", title: "Eliminar", onClick: deleteSelectedRectangle, disabled: !selectedRectId }, h("img", { src: "/testdata-assets/eliminar.png", alt: "" }))
    ),
    h("p", { className: status.error ? "testdata-status error" : "testdata-status" }, status.message),
    h(
      "div",
      { className: "testdata-canvas-frame" },
      h("canvas", {
        ref: canvasRef,
        className: session ? "testdata-pdf-canvas" : "testdata-pdf-canvas empty",
        style: session ? { width: `${zoom}%` } : null,
        onMouseDown: (event) => {
          if (!session) return;
          const point = pointer(event);
          const hit = hitTestRectangle(point);
          if (event.detail > 1 && hit?.rect) {
            openRectangleEditor(hit.rect);
            return;
          }
          if (hit) {
            setSelectedRectId(hit.rect.id);
            rememberRectangles();
            interactionRef.current = {
              mode: hit.mode,
              handle: hit.handle,
              rectId: hit.rect.id,
              start: point,
              original: { ...hit.rect },
            };
            return;
          }
          setSelectedRectId(null);
          drawingRef.current = { x1: point.x, y1: point.y, x2: point.x, y2: point.y };
        },
        onMouseMove: (event) => {
          const point = pointer(event);
          if (interactionRef.current) {
            const interaction = interactionRef.current;
            const scale = scaleRef.current;
            const dx = (point.x - interaction.start.x) / scale;
            const dy = (point.y - interaction.start.y) / scale;
            setRectangles((items) =>
              items.map((rect) => {
                if (rect.id !== interaction.rectId) return rect;
                const original = interaction.original;
                if (interaction.mode === "move") {
                  const width = original.x2 - original.x1;
                  const height = original.y2 - original.y1;
                  const x1 = Math.max(0, Math.min(session.width - width, original.x1 + dx));
                  const y1 = Math.max(0, Math.min(session.height - height, original.y1 + dy));
                  return { ...rect, x1, y1, x2: x1 + width, y2: y1 + height };
                }
                const next = { ...rect };
                if (interaction.handle.includes("n")) next.y1 = Math.max(0, original.y1 + dy);
                if (interaction.handle.includes("s")) next.y2 = Math.min(session.height, original.y2 + dy);
                if (interaction.handle.includes("w")) next.x1 = Math.max(0, original.x1 + dx);
                if (interaction.handle.includes("e")) next.x2 = Math.min(session.width, original.x2 + dx);
                return normalizeRect(next);
              })
            );
            return;
          }
          if (!drawingRef.current) return;
          drawingRef.current.x2 = point.x;
          drawingRef.current.y2 = point.y;
          draw();
        },
        onMouseUp: () => {
          if (interactionRef.current) {
            interactionRef.current = null;
            return;
          }
          finishRectangle();
        },
        onDoubleClick: (event) => {
          if (!session) return;
          const hit = hitTestRectangle(pointer(event));
          if (hit?.rect) openRectangleEditor(hit.rect);
        },
      })
    ),
    h(
      "section",
      { className: "testdata-bottom-bar" },
      h("button", { onClick: () => goToPage(page - 1) }, "<"),
      h("button", { onClick: () => goToPage(page + 1) }, ">"),
      h("span", null, "Página"),
      h("input", {
        value: page,
        onChange: (event) => {
          const value = Number(event.target.value);
          if (Number.isInteger(value)) setPage(value);
        },
        onBlur: () => goToPage(page),
      }),
      h("span", null, `de ${session?.page_count || 0}`),
      h("button", { onClick: () => goToPage(page) }, "Ir"),
      h("div", { className: "zoom-controls" }, h("span", null, "Zoom"), h("button", { onClick: () => setZoom(Math.max(30, zoom - 10)) }, "-"), h("span", null, `${zoom}%`), h("button", { onClick: () => setZoom(Math.min(300, zoom + 10)) }, "+"))
    ),
    activeModal === "catalogue" ? h(CatalogueModal, { sections: catalogueSections, onClose: () => setActiveModal(null) }) : null,
    activeModal === "help" ? h(HelpModal, { content: helpContent, onClose: () => setActiveModal(null) }) : null,
    activeModal === "redaction" ? h(RedactionModal, { concepts, form, setForm, histories: classificationHistory, onAccept: acceptPendingRedaction, onCancel: () => (setPendingRect(null), setEditingRectId(null), setActiveModal(null), draw()) }) : null
  );
}

function CatalogueModal({ sections, onClose }) {
  return h(
    Modal,
    { title: "Catálogo de Conceptos", onClose, wide: true },
    h(
      "div",
      { className: "catalogue-columns" },
      (sections || []).map((section) =>
        h(
          "section",
          { key: section.title, className: "catalogue-column" },
          h("h3", null, section.title),
          h(
            "div",
            { className: "catalogue-list" },
            section.items.map((item) => h("p", { key: item.id }, `${item.id}. ${item.name}`))
          )
        )
      )
    )
  );
}

function HelpModal({ content, onClose }) {
  return h(
    Modal,
    { title: content?.title || "Ayuda", onClose },
    h("h3", { className: "modal-heading" }, content?.heading || "Guía de uso"),
    h(
      "div",
      { className: "help-sections" },
      (content?.sections || []).map(([title, bullets]) =>
        h(
          "section",
          { key: title },
          h("h4", null, title),
          bullets.map((bullet) => h("p", { key: bullet }, `• ${bullet}`))
        )
      )
    )
  );
}

function RedactionModal({ concepts, form, setForm, histories, onAccept, onCancel }) {
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
      [
        ["general", "General"],
        ["reserved", "Información Reservada"],
        ["confidential", "Información Confidencial"],
        ["other_law", "Otra Ley"],
      ].map(([id, label]) => h("button", { key: id, className: tab === id ? "active" : "", onClick: () => updateTab(id) }, label))
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
