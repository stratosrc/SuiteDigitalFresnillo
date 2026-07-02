import { h, React } from "/static/js/shared/react.js";
import { responseToBlob, saveBlob } from "/static/js/shared/helpers.js";
import { fetchHelp, normalizeProjectPayload } from "./api.js";
import {
  buildExportSummary,
  DRAFT_KEY,
  emptyArea,
  emptyDirectory,
  emptyPerson,
  hasExportableData,
  normalizeDirectory,
  toDirectoryPayload,
  toProjectPayload,
} from "./constants.js";
import { DirectoryEditor } from "./components/DirectoryEditor.js";
import { HelpModal } from "./components/HelpModal.js";
import { ModuleChrome } from "./components/ModuleChrome.js";

const clampIndex = (index, length) => Math.max(0, Math.min(length - 1, index));

const readJsonFile = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        resolve(JSON.parse(reader.result));
      } catch {
        reject(new Error("El archivo seleccionado no es un proyecto valido."));
      }
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file, "utf-8");
  });

const loadInitialDirectory = () => {
  try {
    const draft = localStorage.getItem(DRAFT_KEY);
    if (draft) return normalizeDirectory(JSON.parse(draft));
  } catch {
    localStorage.removeItem(DRAFT_KEY);
  }
  return emptyDirectory();
};

export default function Directory() {
  const [directory, setDirectory] = React.useState(loadInitialDirectory);
  const [help, setHelp] = React.useState(null);
  const [helpOpen, setHelpOpen] = React.useState(false);
  const [status, setStatus] = React.useState({ message: "" });
  const fileInputRef = React.useRef(null);

  React.useEffect(() => {
    localStorage.setItem(DRAFT_KEY, JSON.stringify(normalizeDirectory(directory)));
  }, [directory]);

  React.useEffect(() => {
    const handleShortcuts = (event) => {
      if (!event.ctrlKey) return;
      const key = event.key.toLowerCase();
      if (key === "n") {
        event.preventDefault();
        handleNew();
      }
      if (key === "o") {
        event.preventDefault();
        handleOpen();
      }
      if (key === "s") {
        event.preventDefault();
        handleSave();
      }
    };
    window.addEventListener("keydown", handleShortcuts);
    return () => window.removeEventListener("keydown", handleShortcuts);
  });

  const updateDirectory = (patch) => setDirectory((current) => ({ ...current, ...patch }));

  const updateArea = (areaIndex, patch) =>
    setDirectory((current) => ({
      ...current,
      areas: current.areas.map((area, index) => (index === areaIndex ? { ...area, ...patch } : area)),
    }));

  const updatePerson = (areaIndex, personIndex, patch) =>
    setDirectory((current) => ({
      ...current,
      areas: current.areas.map((area, index) =>
        index === areaIndex
          ? {
              ...area,
              personnel: area.personnel.map((person, pIndex) =>
                pIndex === personIndex ? { ...person, ...patch } : person
              ),
            }
          : area
      ),
    }));

  const addArea = () =>
    setDirectory((current) => ({
      ...current,
      areas: [...current.areas, emptyArea()],
    }));

  const removeArea = (areaIndex) =>
    setDirectory((current) => ({
      ...current,
      areas: current.areas.length > 1 ? current.areas.filter((_, index) => index !== areaIndex) : current.areas,
    }));

  const moveArea = (areaIndex, delta) =>
    setDirectory((current) => {
      if (!Number.isFinite(delta) || delta === 0) return current;
      const nextIndex = clampIndex(areaIndex + delta, current.areas.length);
      if (nextIndex === areaIndex) return current;
      const areas = [...current.areas];
      const [area] = areas.splice(areaIndex, 1);
      areas.splice(nextIndex, 0, area);
      return { ...current, areas };
    });

  const addPerson = (areaIndex) =>
    setDirectory((current) => ({
      ...current,
      areas: current.areas.map((area, index) =>
        index === areaIndex ? { ...area, personnel: [...area.personnel, emptyPerson()] } : area
      ),
    }));

  const removePerson = (areaIndex, personIndex) =>
    setDirectory((current) => ({
      ...current,
      areas: current.areas.map((area, index) =>
        index === areaIndex && area.personnel.length > 1
          ? { ...area, personnel: area.personnel.filter((_, pIndex) => pIndex !== personIndex) }
          : area
      ),
    }));

  const movePerson = (areaIndex, personIndex, delta) =>
    setDirectory((current) => {
      if (!Number.isFinite(delta) || delta === 0) return current;
      const areas = current.areas.map((area) => ({ ...area, personnel: [...area.personnel] }));
      const personnel = areas[areaIndex].personnel;
      const nextIndex = clampIndex(personIndex + delta, personnel.length);
      if (nextIndex === personIndex) return current;
      const [person] = personnel.splice(personIndex, 1);
      personnel.splice(nextIndex, 0, person);
      return { ...current, areas };
    });

  const transferPerson = (areaIndex, personIndex, targetAreaIndex) =>
    setDirectory((current) => {
      if (areaIndex === targetAreaIndex) return current;
      const areas = current.areas.map((area) => ({ ...area, personnel: [...area.personnel] }));
      const [person] = areas[areaIndex].personnel.splice(personIndex, 1);
      areas[targetAreaIndex].personnel.push(person);
      if (areas[areaIndex].personnel.length === 0) areas[areaIndex].personnel.push(emptyPerson());
      return { ...current, areas };
    });

  const handleNew = () => {
    if (!window.confirm("Desea iniciar un proyecto nuevo? Se limpiara el formulario actual.")) return;
    setDirectory(emptyDirectory());
    setStatus({ message: "Proyecto nuevo listo." });
  };

  const handleOpen = () => fileInputRef.current?.click();

  const handleFileSelected = async (event) => {
    const [file] = event.target.files || [];
    event.target.value = "";
    if (!file) return;
    setStatus({ message: "Cargando proyecto..." });
    try {
      const payload = await readJsonFile(file);
      const loaded = await normalizeProjectPayload(payload);
      setDirectory(loaded);
      setStatus({ message: `Proyecto cargado: ${file.name}` });
    } catch (error) {
      setStatus({ message: error.message, error: true });
    }
  };

  const handleSave = async () => {
    const blob = new Blob([JSON.stringify(toProjectPayload(directory), null, 2)], { type: "application/json" });
    const result = await saveBlob(blob, "directorio.dir", [
      { description: "Proyecto de Directorio", accept: { "application/json": [".dir"] } },
    ]);
    if (result !== "cancelled") setStatus({ message: "Proyecto guardado." });
  };

  const handleExport = async () => {
    if (!hasExportableData(directory)) {
      setStatus({ message: "Completa al menos el titulo y un dato del directorio antes de exportar.", error: true });
      return;
    }
    if (!window.confirm(buildExportSummary(directory))) return;
    setStatus({ message: "Generando PDF..." });
    try {
      const response = await fetch("/api/directorio/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(toDirectoryPayload(directory)),
      });
      const blob = await responseToBlob(response);
      const result = await saveBlob(blob, "directorio.pdf", [
        { description: "Documento PDF", accept: { "application/pdf": [".pdf"] } },
      ]);
      setStatus({ message: result === "cancelled" ? "Exportacion cancelada." : "PDF generado." });
    } catch (error) {
      setStatus({ message: error.message, error: true });
    }
  };

  const handleHelp = async () => {
    try {
      if (!help) setHelp(await fetchHelp());
      setHelpOpen(true);
    } catch (error) {
      setStatus({ message: error.message, error: true });
    }
  };

  return h(
    ModuleChrome,
    {
      onNew: handleNew,
      onOpen: handleOpen,
      onSave: handleSave,
      onExport: handleExport,
      onHelp: handleHelp,
      status,
    },
    h("input", {
      ref: fileInputRef,
      type: "file",
      accept: ".dir,application/json",
      className: "hidden-file-input",
      onChange: handleFileSelected,
    }),
    h(DirectoryEditor, {
      directory,
      onAddArea: addArea,
      onAddPerson: addPerson,
      onMoveArea: moveArea,
      onMovePerson: movePerson,
      onRemoveArea: removeArea,
      onRemovePerson: removePerson,
      onTransferPerson: transferPerson,
      onUpdateArea: updateArea,
      onUpdateDirectory: updateDirectory,
      onUpdatePerson: updatePerson,
    }),
    helpOpen ? h(HelpModal, { help, onClose: () => setHelpOpen(false) }) : null
  );
}
