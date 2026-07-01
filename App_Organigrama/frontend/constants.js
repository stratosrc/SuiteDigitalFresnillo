export const CELL_W = 250;
export const CELL_H = 260;
export const NODE_W = 210;
export const NODE_MIN_H = 87;
export const NODE_LOGO_URL = "/organigrama-assets/logo_personal.png";
export const PORTS = ["top", "right", "bottom", "left"];
export const PERSON_BULLET = "\u2022 ";
export const PRIMARY_BLUE = "#09519F";
export const SECONDARY_BLUE = "#3C8AC9";
export const LIGHT_BLUE = "#9DC3E6";
export const NEUTRAL_GRAY = "#797E85";

export const NODE_BASE_STYLE = {
  width: NODE_W,
  minHeight: NODE_MIN_H,
  nameFontSize: 14,
  roleFontSize: 12,
  textPaddingX: 23,
  textPaddingTop: 27,
  textPaddingBottom: 5,
  textGap: 5,
  logoRadius: 44,
  logoCenterOffsetY: -17,
  connectionLineWidth: 2.1,
};

export const HIERARCHY_STYLE_BY_COLOR = {
  [PRIMARY_BLUE]: { widthScale: 1.08, minHeightScale: 1.08, nameFontScale: 1.08, roleFontScale: 1.04 },
  [SECONDARY_BLUE]: { widthScale: 1.04, minHeightScale: 1.03, nameFontScale: 1.03, roleFontScale: 1.01 },
  [LIGHT_BLUE]: { widthScale: 1, minHeightScale: 1, nameFontScale: 1, roleFontScale: 1 },
  [NEUTRAL_GRAY]: { widthScale: 0.98, minHeightScale: 0.98, nameFontScale: 0.96, roleFontScale: 0.96 },
};

export const NODE_HIERARCHY_RANK_BY_COLOR = {
  [PRIMARY_BLUE]: 4,
  [SECONDARY_BLUE]: 3,
  [LIGHT_BLUE]: 2,
  [NEUTRAL_GRAY]: 1,
};

export const COLOR_ROLE_LABELS = {
  [PRIMARY_BLUE]: "Secretarios",
  [SECONDARY_BLUE]: "Directores",
  [LIGHT_BLUE]: "Coordinadores, Jefes o Encargados de Departamento",
  [NEUTRAL_GRAY]: "Personal Administrativo",
};

export const DEFAULT_PALETTE = [
  { label: COLOR_ROLE_LABELS[PRIMARY_BLUE], value: PRIMARY_BLUE },
  { label: COLOR_ROLE_LABELS[SECONDARY_BLUE], value: SECONDARY_BLUE },
  { label: COLOR_ROLE_LABELS[LIGHT_BLUE], value: LIGHT_BLUE },
  { label: COLOR_ROLE_LABELS[NEUTRAL_GRAY], value: NEUTRAL_GRAY },
];

export const emptyDocument = () => ({
  title: "",
  period: "",
  page_orientation: "horizontal",
  show_logos: true,
  nodes: {},
  connections: [],
  blocked_points: [],
});

export const projectPayload = (document) => ({ app: "organigrama", schema_version: 3, document });
