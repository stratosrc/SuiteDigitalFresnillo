import { useMemo } from "react";
import { createRoot } from "react-dom/client";
import Converter from "./modules/Converter.js";
import Directory from "./modules/Directory.js";
import Launcher from "./modules/Launcher.js";
import Organization from "./modules/Organization.js";
import TestData from "./modules/TestData.js";
import { usePath } from "./shared/helpers.js";
import { Shell } from "./shared/layout.js";
import { h, React } from "./shared/react.js";

function App() {
  const path = usePath();
  const content = useMemo(() => {
    if (path === "/testdata") return h(TestData);
    if (path === "/organigrama") return h(Organization);
    if (path === "/directorio") return h(Directory);
    if (path === "/conversor-pdf") return h(Converter);
    return h(Launcher);
  }, [path]);
  return h(React.Fragment, null, h(Shell, { path }), content);
}

createRoot(document.getElementById("root")).render(h(App));
