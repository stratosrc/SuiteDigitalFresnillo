import { copyrightText, modules } from "../shared/constants.js";
import { navigate } from "../shared/helpers.js";
import { h } from "../shared/react.js";

export default function Launcher() {
  return h(
    "main",
    { className: "launcher-window" },
    h(
      "section",
      { className: "launcher-scroll-panel" },
      h(
        "div",
        { className: "launcher-grid" },
        modules.map((item) =>
          h(
            "button",
            { key: item.id, className: "desktop-card", onClick: () => navigate(item.path) },
            h("img", { src: item.icon, alt: "" }),
            h("strong", null, item.name),
            h("span", null, item.description)
          )
        )
      )
    ),
    h("footer", { className: "suite-footer" }, copyrightText)
  );
}
