import { normalizeDirectory } from "./constants.js";

const jsonHeaders = { "Content-Type": "application/json" };

export async function fetchHelp() {
  const response = await fetch("/api/directorio/help");
  if (!response.ok) throw new Error("No se pudo cargar la ayuda.");
  return response.json();
}

export async function normalizeProjectPayload(payload) {
  const response = await fetch("/api/directorio/project/normalize", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    let message = "No se pudo cargar el proyecto.";
    try {
      const body = await response.json();
      message = body.detail || message;
    } catch {
      message = await response.text();
    }
    throw new Error(message);
  }
  const body = await response.json();
  return normalizeDirectory(body.directory);
}
