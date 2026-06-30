export async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    let message = "No se pudo completar la operacion.";
    try {
      const body = await response.json();
      message = body.detail || message;
    } catch {
      message = await response.text();
    }
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return response.json();
}

export const loadPalette = async () => {
  const response = await fetch("/api/organigrama/palette");
  if (!response.ok) throw new Error("No se pudo cargar la paleta.");
  return response.json();
};

export const loadHelp = async () => {
  const response = await fetch("/api/organigrama/help");
  if (!response.ok) throw new Error("No se pudo cargar la ayuda.");
  return response.json();
};
