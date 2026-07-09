import { h, React } from "/static/js/shared/react.js";
import { assetUrl } from "../constants.js";

export function HoverIcon({ base, hover, className = "" }) {
  const [hovered, setHovered] = React.useState(false);
  return h("img", {
    className: `converter-hero-icon ${className}`.trim(),
    src: assetUrl(hovered ? hover : base),
    alt: "",
    onMouseEnter: () => setHovered(true),
    onMouseLeave: () => setHovered(false),
  });
}
