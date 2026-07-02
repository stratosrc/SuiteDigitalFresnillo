import { h, React } from "/static/js/shared/react.js";
import { ASSET_BASE } from "../constants.js";

export function IconButton({ icon, hoverIcon, label, onClick, disabled = false, className = "" }) {
  const [hovered, setHovered] = React.useState(false);
  const source = hovered && hoverIcon ? hoverIcon : icon;
  return h(
    "button",
    {
      type: "button",
      className: `dir-icon-button ${className}`.trim(),
      disabled,
      title: label,
      "aria-label": label,
      onClick,
      onMouseEnter: () => setHovered(true),
      onMouseLeave: () => setHovered(false),
    },
    h("img", { src: `${ASSET_BASE}/${source}`, alt: "" })
  );
}
