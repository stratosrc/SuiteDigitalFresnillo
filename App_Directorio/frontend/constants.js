export const ASSET_BASE = "/module-static/directorio/assets";
export const DRAFT_KEY = "suite-digital-directorio-draft";

let localIdSequence = 0;

export const makeLocalId = () => {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  localIdSequence += 1;
  return `directorio-local-${Date.now()}-${localIdSequence}`;
};

export const emptyPerson = () => ({
  localId: makeLocalId(),
  rank: "",
  name: "",
  position: "",
  email: "",
  start_date: "",
});

export const emptyArea = () => ({
  name: "",
  personnel: [emptyPerson()],
});

export const emptyDirectory = () => ({
  title: "",
  period: "",
  areas: [emptyArea()],
});

export const toProjectPayload = (directory) => ({
  app: "directorio",
  version: 1,
  directory: toDirectoryPayload(directory),
});

export const toDirectoryPayload = (directory = {}) => ({
  title: String(directory.title || ""),
  period: String(directory.period || ""),
  areas: (Array.isArray(directory.areas) ? directory.areas : []).map((area) => ({
    name: String(area.name || ""),
    personnel: (Array.isArray(area.personnel) ? area.personnel : []).map((person) => ({
      rank: String(person.rank || ""),
      name: String(person.name || ""),
      position: String(person.position || ""),
      email: String(person.email || ""),
      start_date: String(person.start_date || ""),
    })),
  })),
});

export const normalizeDirectory = (directory = {}) => {
  const areas = Array.isArray(directory.areas) ? directory.areas : [];
  return {
    title: String(directory.title || ""),
    period: String(directory.period || ""),
    areas: (areas.length ? areas : [emptyArea()]).map((area) => {
      const personnel = Array.isArray(area.personnel) ? area.personnel : [];
      return {
        name: String(area.name || ""),
        personnel: (personnel.length ? personnel : [emptyPerson()]).map((person) => ({
          localId: person.localId || makeLocalId(),
          rank: String(person.rank || ""),
          name: String(person.name || ""),
          position: String(person.position || ""),
          email: String(person.email || ""),
          start_date: String(person.start_date || ""),
        })),
      };
    }),
  };
};

export const hasExportableData = (directory) =>
  Boolean(
    directory.title?.trim() &&
      directory.areas?.some(
        (area) =>
          area.name?.trim() ||
          area.personnel?.some((person) =>
            [person.rank, person.name, person.position, person.email, person.start_date].some((value) => value?.trim())
          )
      )
  );

export const buildExportSummary = (directory) => {
  const areaCount = directory.areas.length;
  const personCount = directory.areas.reduce(
    (total, area) =>
      total +
      area.personnel.filter((person) =>
        [person.rank, person.name, person.position, person.email, person.start_date].some((value) => value.trim())
      ).length,
    0
  );
  return [
    `Titulo: ${directory.title || "Directorio"}`,
    `Periodo: ${directory.period || "Sin periodo"}`,
    `Areas: ${areaCount}`,
    `Colaboradores: ${personCount}`,
    "",
    "Desea generar el PDF?",
  ].join("\n");
};

export const formatEmailOnBlur = (value) => {
  const trimmed = value.trim();
  if (!trimmed || trimmed.includes("@")) return trimmed;
  return `${trimmed}@fresnillo.gob.mx`;
};
