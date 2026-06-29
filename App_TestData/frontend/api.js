import { cloneRectangles } from "/static/js/shared/helpers.js";

export const loadCatalogue = async () => {
  const response = await fetch("/api/catalogo");
  return response.json();
};

export const loadHelpContent = async () => {
  const response = await fetch("/api/testdata/help");
  return response.json();
};

export const normalizeRedactions = async (sessionId, rectangles) => {
  const response = await fetch("/api/testdata/rectangles/normalize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId || "draft", rectangles }),
  });
  if (!response.ok) return cloneRectangles(rectangles);
  const payload = await response.json();
  return payload.rectangles || cloneRectangles(rectangles);
};

export const deleteRedaction = async (sessionId, rectangles, selectedRectId) => {
  const response = await fetch("/api/testdata/rectangles/delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId || "draft",
      rectangles,
      selected_rect_id: selectedRectId,
    }),
  });
  if (!response.ok) return null;
  return response.json();
};

export const restorePdfFromProject = async (filename, data) => {
  const response = await fetch("/api/testdata/upload-base64", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename: filename || "proyecto.pdf", data }),
  });
  if (!response.ok) throw new Error((await response.json()).detail || "No se pudo restaurar el PDF del proyecto.");
  return response.json();
};
