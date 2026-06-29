import { h } from "/static/js/shared/react.js";

export function PdfCanvas({ canvasRef, session, zoom, cursor, handlers }) {
  return h(
    "div",
    { className: "testdata-canvas-frame" },
    h("canvas", {
      ref: canvasRef,
      className: session ? "testdata-pdf-canvas" : "testdata-pdf-canvas empty",
      style: session ? { width: `${zoom}%`, cursor } : { cursor: "default" },
      ...handlers,
    })
  );
}
