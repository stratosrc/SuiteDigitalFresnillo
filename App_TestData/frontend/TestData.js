import { useEffect, useRef, useState } from "react";
import { cloneRectangles, fileToDataUrl, responseToBlob, saveBlob } from "/static/js/shared/helpers.js";
import { h } from "/static/js/shared/react.js";
import { deleteRedaction, loadCatalogue, loadHelpContent, normalizeRedactions, restorePdfFromProject } from "./api.js";
import { CatalogueModal } from "./components/CatalogueModal.js";
import { HelpModal } from "./components/HelpModal.js";
import { PdfCanvas } from "./components/PdfCanvas.js";
import { RedactionModal } from "./components/RedactionModal.js";
import { TestDataBottomBar } from "./components/TestDataBottomBar.js";
import { TestDataMenu } from "./components/TestDataMenu.js";
import { TestDataToolbar } from "./components/TestDataToolbar.js";
import { defaultRedactionForm, emptyHistory } from "./constants.js";
import { useRedactionCanvas } from "./hooks/useRedactionCanvas.js";

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

  useEffect(() => {
    loadCatalogue()
      .then((payload) => {
        setConcepts(payload.items || []);
        setCatalogueSections(payload.sections || []);
      })
      .catch(() => setConcepts([{ id: 1, name: "Nombre" }]));
    loadHelpContent()
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
    return normalizeRedactions(session?.session_id, items);
  };

  const deleteSelectedRectangle = async () => {
    if (!selectedRectId) return;
    const payload = await deleteRedaction(session?.session_id, rectangles, selectedRectId);
    if (!payload) return;
    replaceRectangles(payload.rectangles || []);
    setSelectedRectId(null);
  };

  const { canvasRef, canvasCursor, canvasHandlers, clearCanvas, draw, loadPage } = useRedactionCanvas({
    session,
    page,
    rectangles,
    setRectangles,
    selectedRectId,
    setSelectedRectId,
    rememberRectangles,
    setPendingRect,
    setEditingRectId,
    setForm,
    setActiveModal,
  });

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
    clearCanvas();
    if (fileInputRef.current) fileInputRef.current.value = "";
    fileInputRef.current?.click();
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
      const blob = await responseToBlob(response);
      const result = await saveBlob(blob, "testado.pdf", [
        {
          description: "Archivo PDF",
          accept: { "application/pdf": [".pdf"] },
        },
      ]);
      setStatus({ message: result === "cancelled" ? "Exportacion cancelada." : "PDF testado generado." });
    } catch (error) {
      setStatus({ message: error.message, error: true });
    }
  };

  const goToPage = (nextPage) => {
    if (!session || nextPage < 1 || nextPage > session.page_count) return;
    setPage(nextPage);
    loadPage(nextPage);
  };

  const saveProject = async () => {
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
    try {
      const result = await saveBlob(blob, "testdata-web.tdweb", [
        {
          description: "Proyecto TestData",
          accept: { "application/json": [".tdweb"] },
        },
      ]);
      setStatus({ message: result === "cancelled" ? "Guardado cancelado." : "Proyecto guardado." });
    } catch (error) {
      setStatus({ message: error.message, error: true });
    }
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
        const restoredSession = await restorePdfFromProject(payload.pdf_name, payload.pdf_data);
        setSession(restoredSession);
        loadPage(nextPage, restoredSession, nextRectangles);
        setStatus({ message: "Proyecto cargado con su PDF." });
      } else {
        setSession(null);
        clearCanvas();
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
    h(TestDataMenu, {
      fileMenuOpen,
      setFileMenuOpen,
      onNew: startNewProject,
      onLoadProject: () => projectInputRef.current?.click(),
      onSaveProject: saveProject,
      onExportPdf: exportPdf,
      onOpenCatalogue: () => setActiveModal("catalogue"),
      onOpenHelp: () => setActiveModal("help"),
    }),
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
    h(TestDataToolbar, {
      onUndo: undo,
      onRedo: redo,
      onDelete: deleteSelectedRectangle,
      canUndo: undoStack.length > 0,
      canRedo: redoStack.length > 0,
      selectedRectId,
    }),
    h("p", { className: status.error ? "testdata-status error" : "testdata-status" }, status.message),
    h(PdfCanvas, { canvasRef, session, zoom, cursor: canvasCursor, handlers: canvasHandlers }),
    h(TestDataBottomBar, {
      page,
      pageCount: session?.page_count || 0,
      zoom,
      onPageInput: setPage,
      onGoToPage: goToPage,
      onZoom: setZoom,
    }),
    activeModal === "catalogue" ? h(CatalogueModal, { sections: catalogueSections, onClose: () => setActiveModal(null) }) : null,
    activeModal === "help" ? h(HelpModal, { content: helpContent, onClose: () => setActiveModal(null) }) : null,
    activeModal === "redaction"
      ? h(RedactionModal, {
          concepts,
          form,
          setForm,
          histories: classificationHistory,
          onAccept: acceptPendingRedaction,
          onCancel: () => (setPendingRect(null), setEditingRectId(null), setActiveModal(null), draw()),
        })
      : null
  );
}
