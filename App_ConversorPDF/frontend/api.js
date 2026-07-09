import { responseToBlob } from "/static/js/shared/helpers.js";

export async function loadHelp() {
  const response = await fetch("/api/conversor/help");
  if (!response.ok) throw new Error("No se pudo cargar la ayuda.");
  return response.json();
}

export async function convertFile(entry) {
  const form = new FormData();
  form.append("source_file", entry.file);
  form.append("selection", entry.selection || "");
  const response = await fetch("/api/conversor/convertir", { method: "POST", body: form });
  return responseToBlob(response);
}

export async function planOutputs(entries) {
  const response = await fetch("/api/conversor/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      items: entries.map((entry) => ({
        id: entry.id,
        filename: entry.file.name,
        selection: entry.selection || "",
        split: Boolean(entry.splitOutput),
      })),
    }),
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "No se pudo preparar la conversion.");
  }
  return response.json();
}

export async function mergeFiles(entries) {
  const form = new FormData();
  entries.forEach((entry) => form.append("files", entry.file));
  const response = await fetch("/api/conversor/unir", { method: "POST", body: form });
  return responseToBlob(response);
}
