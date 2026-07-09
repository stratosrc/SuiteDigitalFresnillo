export const ASSET_BASE = "/module-static/conversor/assets";
export const assetUrl = (name) => `${ASSET_BASE}/${name}?v=20260702`;

export const acceptedConvertTypes = [
  ".pdf",
  ".jpg",
  ".jpeg",
  ".png",
  ".webp",
  ".bmp",
  ".gif",
  ".tif",
  ".tiff",
  ".doc",
  ".docx",
  ".rtf",
  ".odt",
  ".xls",
  ".xlsx",
  ".ods",
  ".csv",
  ".ppt",
  ".pptx",
  ".odp",
].join(",");

export const pdfOnlyTypes = ".pdf,application/pdf";

let localIdSequence = 0;

export const fileEntry = (file) => {
  localIdSequence += 1;
  return {
    id: `${Date.now()}-${localIdSequence}-${file.name}`,
    file,
    selection: "",
    splitOutput: false,
  };
};

export const humanFileSize = (bytes) => {
  if (!Number.isFinite(bytes)) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};
