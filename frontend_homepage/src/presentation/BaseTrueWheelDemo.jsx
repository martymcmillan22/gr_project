import { useState } from "react";

const SIZE = 300;
const CENTER = SIZE / 2;
const RADIUS = SIZE * 0.45;
const ARC_THICKNESS = SIZE * 0.065;
const INNER_RADIUS = RADIUS * 0.34;

function BaseTrueWheelGraphic({ activeQuadrant, onQuadrantSelect }) {
  return (
    <svg viewBox="0 0 300 300" className="basetrue-demo-wheel" role="img" aria-label="BaseTrue quadrant wheel">
      <title>BaseTrue quadrant wheel</title>
      <desc>Interactive demo wheel matching the BaseTrue reference image with thin arc bands and exact quadrant orientation.</desc>

      <rect width={SIZE} height={SIZE} fill="#000000" />

      <defs>
        <path id="basetrue-title-arc" d="M 28 166 A 122 122 0 0 1 272 166" />
      </defs>

      <text
        fontSize="34"
        fontWeight="900"
        letterSpacing="3"
        fill="#111111"
        stroke="#ffd54a"
        strokeWidth="3"
        paintOrder="stroke fill"
      >
        <textPath href="#basetrue-title-arc" startOffset="50%" textAnchor="middle">
          BASE TRUE
        </textPath>
      </text>

      <g>
        <path
          d={`
            M ${CENTER} ${CENTER}
            L ${CENTER - RADIUS} ${CENTER - RADIUS}
            A ${RADIUS} ${RADIUS} 0 0 1 ${CENTER} ${CENTER - RADIUS}
            L ${CENTER} ${CENTER - RADIUS + ARC_THICKNESS}
            A ${RADIUS - ARC_THICKNESS} ${RADIUS - ARC_THICKNESS} 0 0 0 ${CENTER - RADIUS + ARC_THICKNESS} ${CENTER - RADIUS + ARC_THICKNESS}
            Z
          `}
          fill="#4CAF50"
          opacity={activeQuadrant && activeQuadrant !== "green" ? 0.45 : 1}
          onClick={() => onQuadrantSelect("green")}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              onQuadrantSelect("green");
            }
          }}
          role="button"
          tabIndex={0}
          className="basetrue-demo-quadrant"
        />
        <path
          d={`
            M ${CENTER} ${CENTER}
            L ${CENTER + RADIUS} ${CENTER - RADIUS}
            A ${RADIUS} ${RADIUS} 0 0 1 ${CENTER} ${CENTER - RADIUS}
            L ${CENTER} ${CENTER - RADIUS + ARC_THICKNESS}
            A ${RADIUS - ARC_THICKNESS} ${RADIUS - ARC_THICKNESS} 0 0 0 ${CENTER + RADIUS - ARC_THICKNESS} ${CENTER - RADIUS + ARC_THICKNESS}
            Z
          `}
          fill="#E53935"
          opacity={activeQuadrant && activeQuadrant !== "red" ? 0.45 : 1}
          onClick={() => onQuadrantSelect("red")}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              onQuadrantSelect("red");
            }
          }}
          role="button"
          tabIndex={0}
          className="basetrue-demo-quadrant"
        />
        <path
          d={`
            M ${CENTER} ${CENTER}
            L ${CENTER + RADIUS} ${CENTER + RADIUS}
            A ${RADIUS} ${RADIUS} 0 0 1 ${CENTER + RADIUS} ${CENTER}
            L ${CENTER + RADIUS - ARC_THICKNESS} ${CENTER}
            A ${RADIUS - ARC_THICKNESS} ${RADIUS - ARC_THICKNESS} 0 0 0 ${CENTER + RADIUS - ARC_THICKNESS} ${CENTER + RADIUS - ARC_THICKNESS}
            Z
          `}
          fill="#1E88E5"
          opacity={activeQuadrant && activeQuadrant !== "blue" ? 0.45 : 1}
          onClick={() => onQuadrantSelect("blue")}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              onQuadrantSelect("blue");
            }
          }}
          role="button"
          tabIndex={0}
          className="basetrue-demo-quadrant"
        />
        <path
          d={`
            M ${CENTER} ${CENTER}
            L ${CENTER - RADIUS} ${CENTER + RADIUS}
            A ${RADIUS} ${RADIUS} 0 0 1 ${CENTER} ${CENTER + RADIUS}
            L ${CENTER} ${CENTER + RADIUS - ARC_THICKNESS}
            A ${RADIUS - ARC_THICKNESS} ${RADIUS - ARC_THICKNESS} 0 0 0 ${CENTER - RADIUS + ARC_THICKNESS} ${CENTER + RADIUS - ARC_THICKNESS}
            Z
          `}
          fill="#FBC02D"
          opacity={activeQuadrant && activeQuadrant !== "yellow" ? 0.45 : 1}
          onClick={() => onQuadrantSelect("yellow")}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              onQuadrantSelect("yellow");
            }
          }}
          role="button"
          tabIndex={0}
          className="basetrue-demo-quadrant"
        />
      </g>

      <circle cx={CENTER} cy={CENTER} r={RADIUS} fill="none" stroke="#111111" strokeWidth="3" />
      <circle cx={CENTER} cy={CENTER} r={RADIUS - ARC_THICKNESS} fill="none" stroke="#111111" strokeWidth="2" />
      <line x1={CENTER} y1={CENTER - RADIUS} x2={CENTER} y2={CENTER + RADIUS} stroke="#111111" strokeWidth="3" />
      <line x1={CENTER - RADIUS} y1={CENTER} x2={CENTER + RADIUS} y2={CENTER} stroke="#111111" strokeWidth="3" />
      <circle cx={CENTER} cy={CENTER} r={INNER_RADIUS} fill="#ffffff" stroke="#111111" strokeWidth="2" />

      <text x={CENTER - 40} y={CENTER - 65} textAnchor="middle" dominantBaseline="middle" fontSize="26" fontWeight="900" fill="#ffffff" stroke="#2e8b57" strokeWidth="3" paintOrder="stroke fill">12</text>
      <text x={CENTER + 40} y={CENTER - 65} textAnchor="middle" dominantBaseline="middle" fontSize="26" fontWeight="900" fill="#ffffff" stroke="#e53935" strokeWidth="3" paintOrder="stroke fill">1</text>
      <text x={CENTER + 68} y={CENTER + 40} textAnchor="middle" dominantBaseline="middle" fontSize="26" fontWeight="900" fill="#ffffff" stroke="#3559c7" strokeWidth="3" paintOrder="stroke fill">2</text>
      <text x={CENTER - 68} y={CENTER + 40} textAnchor="middle" dominantBaseline="middle" fontSize="26" fontWeight="900" fill="#ffffff" stroke="#d28f07" strokeWidth="3" paintOrder="stroke fill">11</text>

      <text x={CENTER - 90} y={CENTER - 12} textAnchor="middle" dominantBaseline="middle" fontSize="26" fontWeight="900" fill="#ffffff" stroke="#2e8b57" strokeWidth="3" paintOrder="stroke fill">4</text>
      <text x={CENTER - 25} y={CENTER - 12} textAnchor="middle" dominantBaseline="middle" fontSize="26" fontWeight="900" fill="#ffffff" stroke="#2e8b57" strokeWidth="3" paintOrder="stroke fill">8</text>
      <text x={CENTER + 28} y={CENTER - 12} textAnchor="middle" dominantBaseline="middle" fontSize="26" fontWeight="900" fill="#ffffff" stroke="#e53935" strokeWidth="3" paintOrder="stroke fill">5</text>
      <text x={CENTER + 93} y={CENTER + 13} textAnchor="middle" dominantBaseline="middle" fontSize="26" fontWeight="900" fill="#ffffff" stroke="#e53935" strokeWidth="3" paintOrder="stroke fill">9</text>

      <text x={CENTER - 65} y={CENTER + 20} textAnchor="middle" dominantBaseline="middle" fontSize="26" fontWeight="900" fill="#ffffff" stroke="#d28f07" strokeWidth="3" paintOrder="stroke fill">7</text>
      <text x={CENTER - 28} y={CENTER + 100} textAnchor="middle" dominantBaseline="middle" fontSize="26" fontWeight="900" fill="#ffffff" stroke="#d28f07" strokeWidth="3" paintOrder="stroke fill">3</text>
      <text x={CENTER + 28} y={CENTER + 52} textAnchor="middle" dominantBaseline="middle" fontSize="26" fontWeight="900" fill="#ffffff" stroke="#3559c7" strokeWidth="3" paintOrder="stroke fill">6</text>
      <text x={CENTER + 24} y={CENTER + 110} textAnchor="middle" dominantBaseline="middle" fontSize="26" fontWeight="900" fill="#ffffff" stroke="#3559c7" strokeWidth="3" paintOrder="stroke fill">10</text>

      <circle cx={CENTER} cy={CENTER} r="4" fill="#111111" />
    </svg>
  );
}

export default function BaseTrueWheelDemo() {
  const [activeQuadrant, setActiveQuadrant] = useState(null);

  return (
    <section className="panel basetrue-demo">
      <div className="basetrue-demo-copy">
        <p className="eyebrow">Component Demo</p>
        <h2>BaseTrue Wheel Preview</h2>
        <p className="status-line">
          An interactive quadrant demo for the BaseTrue UI pipeline. Click a quadrant to highlight it.
        </p>

        <div className="basetrue-demo-chips">
          <span>interactive selection</span>
          <span>keyboard support</span>
          <span>token colors</span>
        </div>
      </div>

      <div className="basetrue-demo-art">
        <BaseTrueWheelGraphic activeQuadrant={activeQuadrant} onQuadrantSelect={setActiveQuadrant} />
      </div>
    </section>
  );
}