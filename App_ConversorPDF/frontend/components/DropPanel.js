import { h, React } from "/static/js/shared/react.js";

export function DropPanel({ accept, children, className = "", multiple = true, onFiles }) {
  const inputRef = React.useRef(null);
  const [dragging, setDragging] = React.useState(false);

  const handleFiles = (files) => {
    const selected = Array.from(files || []);
    if (selected.length) onFiles(selected);
  };

  return h(
    "button",
    {
      type: "button",
      className: `drop-panel ${className} ${dragging ? "dragging" : ""}`.trim(),
      onClick: () => inputRef.current?.click(),
      onDragEnter: (event) => {
        event.preventDefault();
        setDragging(true);
      },
      onDragOver: (event) => event.preventDefault(),
      onDragLeave: () => setDragging(false),
      onDrop: (event) => {
        event.preventDefault();
        setDragging(false);
        handleFiles(event.dataTransfer.files);
      },
    },
    children,
    h("input", {
      ref: inputRef,
      type: "file",
      accept,
      multiple,
      className: "hidden-file-input",
      onChange: (event) => {
        handleFiles(event.target.files);
        event.target.value = "";
      },
    })
  );
}
