import { h, React } from "/static/js/shared/react.js";

export function PositionInput({ value, className, ariaLabel, onCommit }) {
  const [draft, setDraft] = React.useState(String(value));
  const ignoreNextBlur = React.useRef(false);

  React.useEffect(() => {
    setDraft(String(value));
  }, [value]);

  const commit = (nextDraft = draft) => {
    const parsed = Number.parseInt(nextDraft, 10);
    if (Number.isFinite(parsed)) {
      onCommit(parsed);
      setDraft(String(parsed));
      return;
    }
    setDraft(String(value));
  };

  return h("input", {
    className: `position-input ${className || ""}`.trim(),
    value: draft,
    inputMode: "numeric",
    "aria-label": ariaLabel,
    onChange: (event) => setDraft(event.target.value),
    onBlur: () => {
      if (ignoreNextBlur.current) {
        ignoreNextBlur.current = false;
        return;
      }
      commit();
    },
    onFocus: (event) => event.currentTarget.select(),
    onKeyDown: (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        ignoreNextBlur.current = true;
        commit(event.currentTarget.value);
        event.currentTarget.blur();
      }
      if (event.key === "Escape") {
        setDraft(String(value));
        event.currentTarget.blur();
      }
    },
  });
}
