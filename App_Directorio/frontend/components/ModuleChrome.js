import { h, React } from "/static/js/shared/react.js";
import { navigate } from "/static/js/shared/helpers.js";

export function ModuleChrome({ onNew, onOpen, onSave, onExport, onHelp, children, status }) {
  const [menuOpen, setMenuOpen] = React.useState(false);
  const menuRef = React.useRef(null);

  React.useEffect(() => {
    const close = (event) => {
      if (!menuRef.current?.contains(event.target)) setMenuOpen(false);
    };
    document.addEventListener("pointerdown", close);
    return () => document.removeEventListener("pointerdown", close);
  }, []);

  const menuAction = (handler) => () => {
    setMenuOpen(false);
    handler();
  };

  return h(
    "main",
    { className: "directory-app" },
    h(
      "div",
      { className: "directory-topbar" },
      h(
        "div",
        { className: "directory-menu-wrap", ref: menuRef },
        h(
          "button",
          { type: "button", className: "directory-menu-button", onClick: () => setMenuOpen((value) => !value) },
          "Archivo"
        ),
        menuOpen
          ? h(
              "div",
              { className: "directory-dropdown" },
              h("button", { type: "button", onClick: menuAction(onNew) }, "Nuevo"),
              h("button", { type: "button", onClick: menuAction(onOpen) }, "Cargar proyecto"),
              h("button", { type: "button", onClick: menuAction(onSave) }, "Guardar proyecto"),
              h("button", { type: "button", onClick: menuAction(onExport) }, "Exportar PDF")
            )
          : null
      ),
      h("button", { type: "button", className: "directory-menu-button", onClick: onHelp }, "Ayuda"),
      h("button", { type: "button", className: "directory-exit", onClick: () => navigate("/") }, "Salir")
    ),
    children,
    status?.message ? h("div", { className: status.error ? "directory-status error" : "directory-status" }, status.message) : null
  );
}
