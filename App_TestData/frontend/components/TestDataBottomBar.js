import { h } from "/static/js/shared/react.js";

export function TestDataBottomBar({ page, pageCount, zoom, onPageInput, onGoToPage, onZoom }) {
  return h(
    "section",
    { className: "testdata-bottom-bar" },
    h("button", { onClick: () => onGoToPage(page - 1) }, "<"),
    h("button", { onClick: () => onGoToPage(page + 1) }, ">"),
    h("span", null, "Página"),
    h("input", {
      value: page,
      onChange: (event) => {
        const value = Number(event.target.value);
        if (Number.isInteger(value)) onPageInput(value);
      },
      onBlur: () => onGoToPage(page),
    }),
    h("span", null, `de ${pageCount || 0}`),
    h("button", { onClick: () => onGoToPage(page) }, "Ir"),
    h(
      "div",
      { className: "zoom-controls" },
      h("span", null, "Zoom"),
      h("button", { onClick: () => onZoom(Math.max(30, zoom - 10)) }, "-"),
      h("span", null, `${zoom}%`),
      h("button", { onClick: () => onZoom(Math.min(300, zoom + 10)) }, "+")
    )
  );
}
