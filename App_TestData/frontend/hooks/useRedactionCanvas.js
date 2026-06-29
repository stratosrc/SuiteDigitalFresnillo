import { useEffect, useRef, useState } from "react";
import { normalizeRect } from "/static/js/shared/helpers.js";

export function useRedactionCanvas({
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
}) {
  const [canvasCursor, setCanvasCursor] = useState("crosshair");
  const canvasRef = useRef(null);
  const imageRef = useRef(null);
  const drawingRef = useRef(null);
  const interactionRef = useRef(null);
  const scaleRef = useRef(1);

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
      const height = (rect.y2 - rect.y1) * scale;
      ctx.fillStyle = "rgba(255,255,255,0.72)";
      ctx.strokeStyle = rect.id === selectedRectId ? "#22C55E" : "#263238";
      ctx.lineWidth = rect.id === selectedRectId ? 3 : 2;
      ctx.fillRect(x, y, w, height);
      ctx.strokeRect(x, y, w, height);
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

  const clearCanvas = () => {
    imageRef.current = null;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
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

  const cursorForHit = (hit) => {
    if (!hit) return session ? "crosshair" : "default";
    if (hit.mode === "move") return "move";
    if (hit.handle === "nw" || hit.handle === "se") return "nwse-resize";
    if (hit.handle === "ne" || hit.handle === "sw") return "nesw-resize";
    return "default";
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

  const canvasHandlers = {
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
        setCanvasCursor(cursorForHit(interaction));
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
      if (!drawingRef.current) {
        setCanvasCursor(cursorForHit(hitTestRectangle(point)));
        return;
      }
      setCanvasCursor("crosshair");
      drawingRef.current.x2 = point.x;
      drawingRef.current.y2 = point.y;
      draw();
    },
    onMouseUp: (event) => {
      if (interactionRef.current) {
        setCanvasCursor(cursorForHit(hitTestRectangle(pointer(event))));
        interactionRef.current = null;
        return;
      }
      finishRectangle();
    },
    onMouseLeave: () => setCanvasCursor(session ? "crosshair" : "default"),
    onDoubleClick: (event) => {
      if (!session) return;
      const hit = hitTestRectangle(pointer(event));
      if (hit?.rect) openRectangleEditor(hit.rect);
    },
  };

  return { canvasRef, canvasCursor, canvasHandlers, clearCanvas, draw, loadPage };
}
