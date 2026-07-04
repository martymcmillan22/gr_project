import React from "react";
import StatisticsRelayGroup from "./StatisticsRelayGroup";

const RED = "#d00000";

export default function StatisticsRelayDiagram() {
  return (
    <svg viewBox="0 0 1200 900" width="100%" height="100%" style={{ background: "transparent" }}>
      <circle cx="600" cy="450" r="380" fill="none" stroke={RED} strokeWidth="4" />

      <rect x="420" y="330" width="360" height="240" rx="30" fill="none" stroke={RED} strokeWidth="5" />

      <text x="600" y="420" textAnchor="middle" fill={RED} fontSize="40" fontWeight="700">
        Statistics
      </text>
      <text x="600" y="470" textAnchor="middle" fill={RED} fontSize="22" fontWeight="500">
        Relay
      </text>

      <g transform="translate(180, 80)">
        <StatisticsRelayGroup direction="top" count={6} />
      </g>

      <g transform="translate(180, 700)">
        <StatisticsRelayGroup direction="bottom" count={6} />
      </g>

      <g transform="translate(80, 200) rotate(-90)">
        <StatisticsRelayGroup direction="left" count={5} />
      </g>

      <g transform="translate(980, 200) rotate(90)">
        <StatisticsRelayGroup direction="right" count={5} />
      </g>

      <text x="600" y="40" textAnchor="middle" fill={RED} fontSize="28" fontWeight="700">
        S
      </text>
      <text x="600" y="880" textAnchor="middle" fill={RED} fontSize="28" fontWeight="700">
        C
      </text>
      <text x="40" y="460" textAnchor="middle" fill={RED} fontSize="28" fontWeight="700">
        P
      </text>
      <text x="1160" y="460" textAnchor="middle" fill={RED} fontSize="28" fontWeight="700">
        A
      </text>

      <circle cx="600" cy="450" r="260" fill="none" stroke="rgba(0,0,0,0.08)" />
    </svg>
  );
}
