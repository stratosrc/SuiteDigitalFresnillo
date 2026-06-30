import { CELL_H, CELL_W, HIERARCHY_STYLE_BY_COLOR, NODE_BASE_STYLE, PERSON_BULLET } from "../constants.js";

export function gridToWorld(gridX, gridY) {
  return { x: gridX * CELL_W, y: gridY * CELL_H };
}

export function worldToGrid(world) {
  return { x: Math.round(world.x / CELL_W), y: Math.round(world.y / CELL_H) };
}

export function nodeAtCellId(document, gridX, gridY) {
  return Object.values(document.nodes || {}).find((node) => node.grid_x === gridX && node.grid_y === gridY)?.id || null;
}

export function pointKey(point) {
  return `${Number(point[0])},${Number(point[1])}`;
}

export function peopleToDisplay(name) {
  const people = (name || "").split("\n").map(normalizePersonLine).filter(Boolean);
  return people.length ? people.map((person) => `${PERSON_BULLET}${person}`).join("\n") : PERSON_BULLET;
}

export function displayToPeople(text) {
  return (text || "").split("\n").map(normalizePersonLine).filter(Boolean).join("\n");
}

export function normalizePersonLine(line) {
  return (line || "").trim().replace(/^[\u2022-]\s*/, "").trim();
}

export function screenToWorld(screen, viewport) {
  return { x: (screen.x - viewport.x) / viewport.zoom, y: (screen.y - viewport.y) / viewport.zoom };
}

export function nodeStyle(color) {
  const hierarchy = HIERARCHY_STYLE_BY_COLOR[color] || { widthScale: 1, minHeightScale: 1, nameFontScale: 1, roleFontScale: 1 };
  const nameFontSize = NODE_BASE_STYLE.nameFontSize * hierarchy.nameFontScale;
  const roleFontSize = NODE_BASE_STYLE.roleFontSize * hierarchy.roleFontScale;
  return {
    width: NODE_BASE_STYLE.width * hierarchy.widthScale,
    minHeight: NODE_BASE_STYLE.minHeight * hierarchy.minHeightScale,
    nameFontSize,
    roleFontSize,
    nameLineHeight: nameFontSize * 1.15,
    roleLineHeight: roleFontSize * 1.22,
    textPaddingX: NODE_BASE_STYLE.textPaddingX,
    textPaddingTop: NODE_BASE_STYLE.textPaddingTop,
    textPaddingBottom: NODE_BASE_STYLE.textPaddingBottom,
    textGap: NODE_BASE_STYLE.textGap,
    logoRadius: NODE_BASE_STYLE.logoRadius,
    logoCenterOffsetY: NODE_BASE_STYLE.logoCenterOffsetY,
    connectionLineWidth: NODE_BASE_STYLE.connectionLineWidth,
  };
}

export function estimateTextWidth(text, fontSize) {
  return String(text || "").length * Math.max(4.5, fontSize * 0.56);
}

export function fitNodeTextSize(text, startFontSize, nodeWidth, horizontalPadding) {
  const usableWidth = Math.max(20, nodeWidth - horizontalPadding * 2);
  let fontSize = startFontSize;
  while (fontSize > 6 && estimateTextWidth(text, fontSize) > usableWidth) {
    fontSize -= 0.5;
  }
  return Math.max(6, fontSize);
}

export function wrapText(text, fontSize, nodeWidth, horizontalPadding) {
  const normalized = String(text || "").trim();
  if (!normalized) return [];
  const usableWidth = Math.max(20, nodeWidth - horizontalPadding * 2);
  const estimatedCharWidth = Math.max(4.5, fontSize * 0.56);
  const charsPerLine = Math.max(8, Math.floor(usableWidth / estimatedCharWidth));
  return normalized.split(/\r?\n/).flatMap((paragraph) => wrapParagraph(paragraph, charsPerLine));
}

export function wrapPersonNames(text, fontSize, nodeWidth, horizontalPadding) {
  const names = String(text || "").split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (names.length <= 1) {
    return {
      lines: wrapText(names[0] || "", fontSize, nodeWidth, horizontalPadding).map((line) => ({ text: line, endsPersonBlock: true })),
      hasMultiplePeople: false,
    };
  }

  const usableWidth = Math.max(20, nodeWidth - horizontalPadding * 2);
  const estimatedCharWidth = Math.max(4.5, fontSize * 0.56);
  const charsPerLine = Math.max(8, Math.floor(usableWidth / estimatedCharWidth));
  const lines = [];
  names.forEach((name) => {
    const personLines = wrapParagraph(`${PERSON_BULLET}${name}`, charsPerLine, "  ");
    personLines.forEach((line, index) => lines.push({ text: line, endsPersonBlock: index === personLines.length - 1 }));
  });
  return { lines, hasMultiplePeople: true };
}

export function nodeLayout(node, { includeLogo = true } = {}) {
  const style = nodeStyle(node.color);
  const center = gridToWorld(node.grid_x, node.grid_y);
  const nameWrap = wrapPersonNames(node.name || "ASIGNAR NOMBRE", style.nameFontSize, style.width, style.textPaddingX);
  const roleLines = wrapText(node.role || "", style.roleFontSize, style.width, style.textPaddingX);
  const lines = [];
  let cursorY = style.textPaddingTop;

  nameWrap.lines.forEach((line, index) => {
    const fontSize = fitNodeTextSize(line.text, style.nameFontSize, style.width, style.textPaddingX);
    const lineHeight = fontSize * 1.15;
    lines.push({
      text: line.text,
      top: cursorY,
      fontSize,
      lineHeight,
      isBold: true,
      align: nameWrap.hasMultiplePeople ? "left" : "center",
      isUnderlined: false,
    });
    cursorY += lineHeight;
    if (nameWrap.hasMultiplePeople && line.endsPersonBlock && index < nameWrap.lines.length - 1) {
      cursorY += fontSize * 0.45;
    }
  });

  if (nameWrap.lines.length && roleLines.length) cursorY += style.textGap;

  roleLines.forEach((line) => {
    const fontSize = fitNodeTextSize(line, style.roleFontSize, style.width, style.textPaddingX);
    lines.push({
      text: line,
      top: cursorY,
      fontSize,
      lineHeight: fontSize * 1.22,
      isBold: false,
      align: "center",
      isUnderlined: true,
    });
    cursorY += fontSize * 1.22;
  });

  const contentHeight = Math.max(0, cursorY - style.textPaddingTop);
  const height = Math.max(style.minHeight, style.textPaddingTop + contentHeight + style.textPaddingBottom);
  const top = center.y - height / 2;
  const bottom = center.y + height / 2;
  const logoCenterY = top + style.logoCenterOffsetY;
  const visualTop = includeLogo ? Math.min(top, logoCenterY - style.logoRadius) : top;
  return {
    left: center.x - style.width / 2,
    top,
    right: center.x + style.width / 2,
    bottom,
    width: style.width,
    height,
    center,
    style,
    lines,
    logoCenterX: center.x,
    logoCenterY,
    logoImageSize: style.logoRadius * 1.35,
    visualTop,
    visualBottom: bottom,
  };
}

export function portWorld(node, port) {
  const layout = nodeLayout(node, { includeLogo: false });
  if (port === "top") return { x: layout.center.x, y: layout.top };
  if (port === "bottom") return { x: layout.center.x, y: layout.bottom };
  if (port === "left") return { x: layout.left, y: layout.center.y };
  return { x: layout.right, y: layout.center.y };
}

export function distance(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

export function distanceToSegment(point, a, b) {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  if (dx === 0 && dy === 0) return distance(point, a);
  const t = Math.max(0, Math.min(1, ((point.x - a.x) * dx + (point.y - a.y) * dy) / (dx * dx + dy * dy)));
  return distance(point, { x: a.x + t * dx, y: a.y + t * dy });
}

export function nearestPort(node, screen, viewport) {
  const layout = nodeLayout(node, { includeLogo: false });
  const center = {
    x: layout.center.x * viewport.zoom + viewport.x,
    y: layout.center.y * viewport.zoom + viewport.y,
  };
  const halfWidth = (layout.width * viewport.zoom) / 2;
  const halfHeight = (layout.height * viewport.zoom) / 2;
  const distances = {
    top: Math.abs(screen.y - (center.y - halfHeight)),
    bottom: Math.abs(screen.y - (center.y + halfHeight)),
    left: Math.abs(screen.x - (center.x - halfWidth)),
    right: Math.abs(screen.x - (center.x + halfWidth)),
  };
  return Object.entries(distances).sort((a, b) => a[1] - b[1])[0][0];
}

export function nodeDistanceFromScreen(node, screen, viewport) {
  const layout = nodeLayout(node, { includeLogo: false });
  const left = layout.left * viewport.zoom + viewport.x;
  const top = layout.top * viewport.zoom + viewport.y;
  const right = layout.right * viewport.zoom + viewport.x;
  const bottom = layout.bottom * viewport.zoom + viewport.y;
  const dx = Math.max(left - screen.x, 0, screen.x - right);
  const dy = Math.max(top - screen.y, 0, screen.y - bottom);
  return Math.hypot(dx, dy);
}

function wrapParagraph(paragraph, width, subsequentIndent = "") {
  const words = String(paragraph || "").split(/\s+/).filter(Boolean);
  const lines = [];
  let line = "";
  let firstLine = true;

  words.forEach((word) => {
    let nextWord = word;
    while (nextWord.length > width) {
      const prefix = firstLine ? "" : subsequentIndent;
      const sliceLength = Math.max(1, width - prefix.length);
      lines.push(`${prefix}${nextWord.slice(0, sliceLength)}`);
      nextWord = nextWord.slice(sliceLength);
      firstLine = false;
      line = "";
    }
    if (!nextWord) return;
    const prefix = firstLine ? "" : subsequentIndent;
    const candidate = line ? `${line} ${nextWord}` : `${prefix}${nextWord}`;
    if (candidate.length > width && line) {
      lines.push(line);
      firstLine = false;
      line = `${subsequentIndent}${nextWord}`;
    } else {
      line = candidate;
    }
  });

  if (line) lines.push(line);
  return lines.length ? lines : [String(paragraph || "")];
}
