import React from "react";
import StatisticsRelayCell from "./StatisticsRelayCell";

const GRID_SPACING = 130;

function getRotation(direction) {
  switch (direction) {
    case "top":
      return 180;
    case "bottom":
      return 0;
    case "left":
      return 90;
    case "right":
      return 270;
    default:
      return 0;
  }
}

function generateLabels(index) {
  const patterns = [
    { top: "A", right: "B", bottom: "C", left: "D" },
    { top: "B", right: "C", bottom: "D", left: "A" },
    { top: "C", right: "D", bottom: "A", left: "B" },
    { top: "D", right: "A", bottom: "B", left: "C" },
  ];

  return patterns[index % patterns.length];
}

/**
 * StatisticsRelayGroup
 *
 * Props:
 * x, y        -> position of group
 * direction   -> "top" | "bottom" | "left" | "right"
 * count       -> number of relay cells
 */
export default function StatisticsRelayGroup({ x = 0, y = 0, direction = "top", count = 6 }) {
  const rotation = getRotation(direction);
  const isHorizontal = direction === "top" || direction === "bottom";

  return (
    <g transform={`translate(${x} ${y})`}>
      {Array.from({ length: count }).map((_, i) => {
        const offset = i * GRID_SPACING;
        const posX = isHorizontal ? offset : 0;
        const posY = isHorizontal ? 0 : offset;

        return (
          <StatisticsRelayCell key={i} x={posX} y={posY} rotation={rotation} labels={generateLabels(i)} />
        );
      })}
    </g>
  );
}
