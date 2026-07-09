import { saveBlob } from "/static/js/shared/helpers.js";
import { h, React } from "/static/js/shared/react.js";
import { convertFile, loadHelp, mergeFiles, planOutputs } from "./api.js";
import { fileEntry } from "./constants.js";
import { ConverterShell } from "./components/ConverterShell.js";
import { ConvertPanel } from "./components/ConvertPanel.js";
import { HelpModal } from "./components/HelpModal.js";
import { MergePanel } from "./components/MergePanel.js";

const appendEntries = (current, files, pdfOnly = false) => {
  const existing = new Set(current.map((entry) => `${entry.file.name}:${entry.file.size}:${entry.file.lastModified}`));
  const next = [...current];
  files.forEach((file) => {
    if (pdfOnly && !file.name.toLowerCase().endsWith(".pdf")) return;
    const key = `${file.name}:${file.size}:${file.lastModified}`;
    if (!existing.has(key)) {
      existing.add(key);
      next.push(fileEntry(file));
    }
  });
  return next;
};

const pdfPickerTypes = [{ description: "Documento PDF", accept: { "application/pdf": [".pdf"] } }];

export default function Converter() {
  const [activeTab, setActiveTab] = React.useState("convert");
  const [convertEntries, setConvertEntries] = React.useState([]);
  const [convertedOutputs, setConvertedOutputs] = React.useState([]);
  const [mergeEntries, setMergeEntries] = React.useState([]);
  const [help, setHelp] = React.useState(null);
  const [helpOpen, setHelpOpen] = React.useState(false);
  const [status, setStatus] = React.useState({ message: "" });

  React.useEffect(() => {
    let cancelled = false;
    if (!convertEntries.length) {
      setConvertedOutputs([]);
      return () => {
        cancelled = true;
      };
    }
    planOutputs(convertEntries)
      .then((plan) => {
        if (!cancelled) setConvertedOutputs(plan.outputs);
      })
      .catch((error) => {
        if (!cancelled) {
          setConvertedOutputs([]);
          setStatus({ message: error.message, error: true });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [convertEntries]);

  const resetActive = () => {
    if (activeTab === "merge") {
      setMergeEntries([]);
    } else {
      setConvertEntries([]);
      setConvertedOutputs([]);
    }
    setStatus({ message: "Listo para comenzar." });
  };

  const openHelp = async () => {
    try {
      if (!help) setHelp(await loadHelp());
      setHelpOpen(true);
    } catch (error) {
      setStatus({ message: error.message, error: true });
    }
  };

  const downloadOutput = async (output) => {
    const entry = convertEntries.find((item) => item.id === output.sourceId);
    if (!entry) return;
    setStatus({ message: `Convirtiendo ${output.filename}...` });
    try {
      const blob = await convertFile({ ...entry, selection: output.selection || "" });
      const result = await saveBlob(blob, output.filename, pdfPickerTypes);
      setStatus({ message: result === "cancelled" ? "Descarga cancelada." : `${output.filename} descargado.` });
    } catch (error) {
      setStatus({ message: error.message, error: true });
    }
  };

  const downloadAllOutputs = async () => {
    const entriesById = new Map(convertEntries.map((entry) => [entry.id, entry]));
    for (const output of convertedOutputs) {
      const entry = entriesById.get(output.sourceId);
      if (!entry) continue;
      setStatus({ message: `Convirtiendo ${output.filename}...` });
      try {
        const blob = await convertFile({ ...entry, selection: output.selection || "" });
        const result = await saveBlob(blob, output.filename, pdfPickerTypes);
        if (result === "cancelled") {
          setStatus({ message: "Descarga cancelada." });
          return;
        }
      } catch (error) {
        setStatus({ message: error.message, error: true });
        return;
      }
    }
    setStatus({ message: "PDFs descargados." });
  };

  const runMerge = async () => {
    if (mergeEntries.length < 2) {
      setStatus({ message: "Selecciona al menos dos PDFs para unir.", error: true });
      return;
    }
    setStatus({ message: "Uniendo PDFs..." });
    try {
      const blob = await mergeFiles(mergeEntries);
      const result = await saveBlob(blob, "pdfs_unidos.pdf", pdfPickerTypes);
      setStatus({ message: result === "cancelled" ? "Union cancelada." : "PDF unido correctamente." });
    } catch (error) {
      setStatus({ message: error.message, error: true });
    }
  };

  const reorderMerge = (sourceIndex, targetIndex) => {
    setMergeEntries((current) => {
      if (sourceIndex === targetIndex || sourceIndex < 0 || sourceIndex >= current.length) return current;
      const next = [...current];
      const [item] = next.splice(sourceIndex, 1);
      const adjustedTarget = targetIndex > sourceIndex ? targetIndex - 1 : targetIndex;
      next.splice(Math.max(0, Math.min(adjustedTarget, next.length)), 0, item);
      return next;
    });
  };

  return h(
    ConverterShell,
    {
      activeTab,
      onNew: resetActive,
      onHelp: openHelp,
      onTabChange: setActiveTab,
      status,
    },
    activeTab === "convert"
      ? h(ConvertPanel, {
          entries: convertEntries,
          outputs: convertedOutputs,
          onAddFiles: (files) => {
            setConvertEntries((current) => appendEntries(current, files));
          },
          onDownloadAll: downloadAllOutputs,
          onDownloadOutput: downloadOutput,
          onRemoveEntry: (id) => {
            setConvertEntries((current) => current.filter((entry) => entry.id !== id));
            setConvertedOutputs((current) => current.filter((output) => output.sourceId !== id));
          },
          onSelectionChange: (id, selection) =>
            setConvertEntries((current) => current.map((entry) => (entry.id === id ? { ...entry, selection } : entry))),
          onToggleSplit: (id) => {
            setConvertEntries((current) =>
              current.map((entry) => (entry.id === id ? { ...entry, splitOutput: !entry.splitOutput } : entry))
            );
          },
        })
      : h(MergePanel, {
          entries: mergeEntries,
          onAddFiles: (files) => setMergeEntries((current) => appendEntries(current, files, true)),
          onMerge: runMerge,
          onRemoveEntry: (id) => setMergeEntries((current) => current.filter((entry) => entry.id !== id)),
          onReorder: reorderMerge,
        }),
    helpOpen ? h(HelpModal, { content: help, onClose: () => setHelpOpen(false) }) : null
  );
}
