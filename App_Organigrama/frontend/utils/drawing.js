import { CELL_H, CELL_W, NODE_BASE_STYLE } from "../constants.js";

export function drawGrid(ctx, box, viewport) {
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, box.width, box.height);
  ctx.lineWidth = 1;
  const stepX = CELL_W * viewport.zoom;
  const stepY = CELL_H * viewport.zoom;
  const startColumn = Math.floor(-viewport.x / stepX) - 1;
  const endColumn = Math.ceil((box.width - viewport.x) / stepX) + 1;
  const startRow = Math.floor(-viewport.y / stepY) - 1;
  const endRow = Math.ceil((box.height - viewport.y) / stepY) + 1;

  for (let column = startColumn; column <= endColumn; column += 1) {
    const x = viewport.x + column * stepX;
    ctx.strokeStyle = column === 0 ? "#cbd8e3" : "#e7eef5";
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, box.height);
    ctx.stroke();
  }

  for (let row = startRow; row <= endRow; row += 1) {
    const y = viewport.y + row * stepY;
    ctx.strokeStyle = row === 0 ? "#cbd8e3" : "#e7eef5";
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(box.width, y);
    ctx.stroke();
  }
}

export function drawArrow(ctx, screenPoints, { length = 12, width = 11, targetGap = 10 } = {}) {
  const arrow = buildArrowTriangle(screenPoints, { length, width, targetGap });
  if (!arrow) return;
  ctx.beginPath();
  arrow.forEach((point, index) => {
    if (index === 0) ctx.moveTo(point.x, point.y);
    else ctx.lineTo(point.x, point.y);
  });
  ctx.closePath();
  ctx.fillStyle = ctx.strokeStyle;
  ctx.fill();
}

export function drawEmpty(ctx, box) {
  ctx.fillStyle = "#4b6791";
  ctx.textAlign = "center";
  ctx.textBaseline = "alphabetic";
  ctx.font = "18px Segoe UI, Arial";
  ctx.fillText("Organigrama vacio", box.width / 2, box.height / 2 - 20);
  ctx.font = "16px Segoe UI, Arial";
  ctx.fillText("Haz clic en una celda para crear el primer nodo.", box.width / 2, box.height / 2 + 6);
  ctx.fillText("Tambien puedes abrir un proyecto con Ctrl+O.", box.width / 2, box.height / 2 + 30);
}

export function drawNodeGhost(ctx, cell, viewport) {
  const center = {
    x: cell.x * CELL_W * viewport.zoom + viewport.x,
    y: cell.y * CELL_H * viewport.zoom + viewport.y,
  };
  const width = NODE_BASE_STYLE.width * viewport.zoom;
  const height = NODE_BASE_STYLE.minHeight * viewport.zoom;
  ctx.save();
  ctx.globalAlpha = 0.46;
  ctx.fillStyle = "#9DC3E6";
  ctx.strokeStyle = "#09519F";
  ctx.lineWidth = 2;
  ctx.setLineDash([6, 4]);
  ctx.beginPath();
  ctx.roundRect(center.x - width / 2, center.y - height / 2, width, height, Math.max(0, 12 * viewport.zoom));
  ctx.fill();
  ctx.stroke();
  ctx.globalAlpha = 0.95;
  ctx.fillStyle = "#09519F";
  ctx.font = `700 ${Math.max(6, 8 * viewport.zoom)}px Segoe UI, Arial`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("Nuevo nodo", center.x, center.y);
  ctx.restore();
}

export function drawConnectionDraft(ctx, draft) {
  if (!draft) return;
  ctx.save();
  ctx.setLineDash([8, 5]);
  ctx.strokeStyle = "#f59e0b";
  ctx.lineWidth = Math.max(2, 2 * draft.zoom);
  ctx.beginPath();
  ctx.moveTo(draft.start.x, draft.start.y);
  ctx.lineTo(draft.end.x, draft.end.y);
  ctx.stroke();
  drawArrow(ctx, [draft.start, draft.end], {
    length: Math.max(8, 12 * draft.zoom),
    width: Math.max(8, 11 * draft.zoom),
    targetGap: Math.max(7, 10 * draft.zoom),
  });
  ctx.restore();
}

function buildArrowTriangle(routePoints, { length, width, targetGap }) {
  if (!routePoints || routePoints.length < 2) return null;
  const end = routePoints.at(-1);
  let start = null;
  for (let index = routePoints.length - 2; index >= 0; index -= 1) {
    const candidate = routePoints[index];
    if (candidate.x !== end.x || candidate.y !== end.y) {
      start = candidate;
      break;
    }
  }
  if (!start) return null;
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const segmentLength = Math.hypot(dx, dy);
  if (segmentLength <= 0) return null;
  const directionX = dx / segmentLength;
  const directionY = dy / segmentLength;
  const effectiveGap = Math.min(targetGap, Math.max(0, segmentLength * 0.35));
  const effectiveLength = Math.min(length, Math.max(3, segmentLength - effectiveGap));
  const tip = { x: end.x - directionX * effectiveGap, y: end.y - directionY * effectiveGap };
  const baseCenter = { x: tip.x - directionX * effectiveLength, y: tip.y - directionY * effectiveLength };
  const perpendicularX = -directionY;
  const perpendicularY = directionX;
  const halfWidth = width / 2;
  return [
    tip,
    { x: baseCenter.x + perpendicularX * halfWidth, y: baseCenter.y + perpendicularY * halfWidth },
    { x: baseCenter.x - perpendicularX * halfWidth, y: baseCenter.y - perpendicularY * halfWidth },
  ];
}
