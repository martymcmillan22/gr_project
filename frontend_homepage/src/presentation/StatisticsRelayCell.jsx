import React from "react";

const RED = "#d00000";
const GREEN = "#00aa44";
const YELLOW = "#d6c800";
const BLUE = "#3b82f6";

/**
 * StatisticsRelayCell
 *
 * Props:
 * x, y        -> position
 * rotation    -> 0, 90, 180, 270
 * scale       -> size multiplier
 * labels      -> { top, right, bottom, left }
 */
export default function StatisticsRelayCell({
  x = 0,
  y = 0,
  rotation = 0,
  scale = 1,
  labels = {
    top: "A",
    right: "B",
    bottom: "C",
    left: "D",
  },
}) {
  const W = 120;
  const H = 120;

  return (
    <g
      transform={`
        translate(${x} ${y})
        rotate(${rotation} ${W / 2} ${H / 2})
        scale(${scale})
      `}
    >
      <rect x="5" y="5" width="110" height="110" rx="8" ry="8" fill="none" stroke={GREEN} strokeWidth="3" />

      <rect x="18" y="18" width="84" height="84" fill="none" stroke={YELLOW} strokeWidth="2" />

      <line x1="60" y1="18" x2="60" y2="102" stroke={GREEN} strokeWidth="2" />
      <line x1="18" y1="60" x2="102" y2="60" stroke={GREEN} strokeWidth="2" />

      <rect x="48" y="-6" width="24" height="12" fill="none" stroke={BLUE} strokeWidth="2" />
      <rect x="114" y="48" width="12" height="24" fill="none" stroke={BLUE} strokeWidth="2" />
      <rect x="48" y="114" width="24" height="12" fill="none" stroke={BLUE} strokeWidth="2" />
      <rect x="-6" y="48" width="12" height="24" fill="none" stroke={BLUE} strokeWidth="2" />

      {[
        [18, 18],
        [102, 18],
        [18, 102],
        [102, 102],
      ].map(([cx, cy], i) => (
        <circle key={i} cx={cx} cy={cy} r="2.5" fill={GREEN} />
      ))}

      <path d="M60 18 L60 5" stroke={GREEN} strokeWidth="2" fill="none" />
      <path d="M102 60 L115 60" stroke={GREEN} strokeWidth="2" fill="none" />
      <path d="M60 102 L60 115" stroke={GREEN} strokeWidth="2" fill="none" />
      <path d="M18 60 L5 60" stroke={GREEN} strokeWidth="2" fill="none" />

      <text x="60" y="14" textAnchor="middle" fill={RED} fontSize="11" fontWeight="700">
        {labels.top}
      </text>
      <text x="108" y="63" textAnchor="start" fill={RED} fontSize="11" fontWeight="700">
        {labels.right}
      </text>
      <text x="60" y="114" textAnchor="middle" fill={RED} fontSize="11" fontWeight="700">
        {labels.bottom}
      </text>
      <text x="12" y="63" textAnchor="end" fill={RED} fontSize="11" fontWeight="700">
        {labels.left}
      </text>

      <circle cx="60" cy="60" r="18" fill="none" stroke={GREEN} strokeWidth="2" />
      <line x1="42" y1="60" x2="78" y2="60" stroke={GREEN} strokeWidth="2" />
      <line x1="60" y1="42" x2="60" y2="78" stroke={GREEN} strokeWidth="2" />

      <polyline points="28,28 40,40 52,28" fill="none" stroke={YELLOW} strokeWidth="2" />
      <polyline points="68,28 80,40 92,28" fill="none" stroke={YELLOW} strokeWidth="2" />
      <polyline points="28,92 40,80 52,92" fill="none" stroke={YELLOW} strokeWidth="2" />
      <polyline points="68,92 80,80 92,92" fill="none" stroke={YELLOW} strokeWidth="2" />
    </g>
  );
}
