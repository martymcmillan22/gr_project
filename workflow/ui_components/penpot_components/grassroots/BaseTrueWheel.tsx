import React from "react";
import { cn } from "../ui/styles";

export type QuadrantId = "green" | "red" | "yellow" | "blue";

export interface BaseTrueWheelProps {
  className?: string;
  activeQuadrant?: QuadrantId | null;
  onQuadrantSelect?: (quadrant: QuadrantId) => void;
  size?: number;
}

export const BaseTrueWheel = React.forwardRef<HTMLDivElement, BaseTrueWheelProps>(
  ({ className, activeQuadrant = null, onQuadrantSelect, size = 300 }, ref) => {
    const dim = size;
    const center = dim / 2;
    const radius = dim * 0.44;
    const arcThickness = dim * 0.065;
    const innerRadius = radius * 0.34;

    const isDimmed = (quadrant: QuadrantId) => activeQuadrant !== null && activeQuadrant !== quadrant;

    return (
      <div className={cn("flex flex-col items-center gap-3", className)} ref={ref}>
        <div className="select-none text-2xl font-bold tracking-wide">
          <span className="text-red-500">B</span>
          <span className="text-blue-500">A</span>
          <span className="text-yellow-400">S</span>
          <span className="text-green-500">E</span>{" "}
          <span className="text-red-500">T</span>
          <span className="text-green-500">R</span>
          <span className="text-yellow-400">U</span>
          <span className="text-blue-500">E</span>
        </div>

        <svg
          width={dim}
          height={dim}
          viewBox={`0 0 ${dim} ${dim}`}
          className="h-auto w-80 max-w-full"
          role="img"
          aria-label="BaseTrue quadrant number wheel"
        >
          <title>BaseTrue quadrant number wheel</title>
          <desc>Interactive quadrant wheel with thin arc bands and exact quadrant orientation.</desc>

          <rect width={dim} height={dim} fill="#000000" />

          <defs>
            <path id="basetrue-title-arc" d={`M ${dim * 0.08} ${dim * 0.20} A ${dim * 0.42} ${dim * 0.42} 0 0 1 ${dim * 0.92} ${dim * 0.20}`} />
          </defs>

          <g>
            {[
              { letter: "B", color: "#ff5a5a", offset: "0%" },
              { letter: "A", color: "#4f79ff", offset: "12%" },
              { letter: "S", color: "#ffd54a", offset: "24%" },
              { letter: "E", color: "#4caf50", offset: "36%" },
              { letter: "T", color: "#ff5a5a", offset: "50%" },
              { letter: "R", color: "#4caf50", offset: "64%" },
              { letter: "U", color: "#ffd54a", offset: "78%" },
              { letter: "E", color: "#4f79ff", offset: "90%" },
            ].map((item) => (
              <text key={item.letter + item.offset} fontSize={dim * 0.11} fontWeight="900" fill={item.color} stroke="#111111" strokeWidth={dim * 0.008} paintOrder="stroke fill">
                <textPath href="#basetrue-title-arc" startOffset={item.offset}>
                  {item.letter}
                </textPath>
              </text>
            ))}
          </g>

          <g>
            <path
              d={`
                M ${center} ${center}
                L ${center - radius} ${center - radius}
                A ${radius} ${radius} 0 0 1 ${center} ${center - radius}
                L ${center} ${center - radius + arcThickness}
                A ${radius - arcThickness} ${radius - arcThickness} 0 0 0 ${center - radius + arcThickness} ${center - radius + arcThickness}
                Z
              `}
              fill="#4CAF50"
              opacity={isDimmed("green") ? 0.4 : 1}
            />
            <path
              d={`
                M ${center} ${center}
                L ${center + radius} ${center - radius}
                A ${radius} ${radius} 0 0 1 ${center} ${center - radius}
                L ${center} ${center - radius + arcThickness}
                A ${radius - arcThickness} ${radius - arcThickness} 0 0 0 ${center + radius - arcThickness} ${center - radius + arcThickness}
                Z
              `}
              fill="#E53935"
              opacity={isDimmed("red") ? 0.4 : 1}
            />
            <path
              d={`
                M ${center} ${center}
                L ${center + radius} ${center + radius}
                A ${radius} ${radius} 0 0 1 ${center + radius} ${center}
                L ${center + radius - arcThickness} ${center}
                A ${radius - arcThickness} ${radius - arcThickness} 0 0 0 ${center + radius - arcThickness} ${center + radius - arcThickness}
                Z
              `}
              fill="#1E88E5"
              opacity={isDimmed("blue") ? 0.4 : 1}
            />
            <path
              d={`
                M ${center} ${center}
                L ${center - radius} ${center + radius}
                A ${radius} ${radius} 0 0 1 ${center} ${center + radius}
                L ${center} ${center + radius - arcThickness}
                A ${radius - arcThickness} ${radius - arcThickness} 0 0 0 ${center - radius + arcThickness} ${center + radius - arcThickness}
                Z
              `}
              fill="#FBC02D"
              opacity={isDimmed("yellow") ? 0.4 : 1}
            />
          </g>

          <g>
            <circle cx={center} cy={center} r={radius} fill="none" stroke="#111111" strokeWidth={dim * 0.01} />
            <circle cx={center} cy={center} r={radius - arcThickness} fill="none" stroke="#111111" strokeWidth={dim * 0.008} />
            <line x1={center} y1={center - radius} x2={center} y2={center + radius} stroke="#111111" strokeWidth={dim * 0.012} />
            <line x1={center - radius} y1={center} x2={center + radius} y2={center} stroke="#111111" strokeWidth={dim * 0.012} />
            <circle cx={center} cy={center} r={innerRadius} fill="#ffffff" stroke="#111111" strokeWidth={dim * 0.008} />
          </g>

          <g>
            <text x={center - radius * 0.32} y={center - radius * 0.55} textAnchor="middle" dominantBaseline="middle" fontSize={dim * 0.1} fontWeight="800" fill="#ffffff" stroke="#2e8b57" strokeWidth={dim * 0.012} paintOrder="stroke fill">
              12
            </text>
            <text x={center + radius * 0.30} y={center - radius * 0.55} textAnchor="middle" dominantBaseline="middle" fontSize={dim * 0.1} fontWeight="800" fill="#ffffff" stroke="#e53935" strokeWidth={dim * 0.012} paintOrder="stroke fill">
              1
            </text>
            <text x={center + radius * 0.32} y={center + radius * 0.18} textAnchor="middle" dominantBaseline="middle" fontSize={dim * 0.1} fontWeight="800" fill="#ffffff" stroke="#3559c7" strokeWidth={dim * 0.012} paintOrder="stroke fill">
              2
            </text>
            <text x={center - radius * 0.35} y={center + radius * 0.18} textAnchor="middle" dominantBaseline="middle" fontSize={dim * 0.1} fontWeight="800" fill="#ffffff" stroke="#d28f07" strokeWidth={dim * 0.012} paintOrder="stroke fill">
              11
            </text>

            <text x={center - radius * 0.70} y={center - radius * 0.10} textAnchor="middle" dominantBaseline="middle" fontSize={dim * 0.1} fontWeight="800" fill="#ffffff" stroke="#2e8b57" strokeWidth={dim * 0.012} paintOrder="stroke fill">
              4
            </text>
            <text x={center - radius * 0.18} y={center - radius * 0.03} textAnchor="middle" dominantBaseline="middle" fontSize={dim * 0.1} fontWeight="800" fill="#ffffff" stroke="#2e8b57" strokeWidth={dim * 0.012} paintOrder="stroke fill">
              8
            </text>
            <text x={center + radius * 0.18} y={center - radius * 0.03} textAnchor="middle" dominantBaseline="middle" fontSize={dim * 0.1} fontWeight="800" fill="#ffffff" stroke="#e53935" strokeWidth={dim * 0.012} paintOrder="stroke fill">
              5
            </text>
            <text x={center + radius * 0.70} y={center + radius * 0.15} textAnchor="middle" dominantBaseline="middle" fontSize={dim * 0.1} fontWeight="800" fill="#ffffff" stroke="#e53935" strokeWidth={dim * 0.012} paintOrder="stroke fill">
              9
            </text>
            <text x={center - radius * 0.45} y={center + radius * 0.10} textAnchor="middle" dominantBaseline="middle" fontSize={dim * 0.1} fontWeight="800" fill="#ffffff" stroke="#d28f07" strokeWidth={dim * 0.012} paintOrder="stroke fill">
              7
            </text>
            <text x={center - radius * 0.25} y={center + radius * 0.70} textAnchor="middle" dominantBaseline="middle" fontSize={dim * 0.1} fontWeight="800" fill="#ffffff" stroke="#d28f07" strokeWidth={dim * 0.012} paintOrder="stroke fill">
              3
            </text>
            <text x={center + radius * 0.22} y={center + radius * 0.33} textAnchor="middle" dominantBaseline="middle" fontSize={dim * 0.1} fontWeight="800" fill="#ffffff" stroke="#3559c7" strokeWidth={dim * 0.012} paintOrder="stroke fill">
              6
            </text>
            <text x={center + radius * 0.18} y={center + radius * 0.72} textAnchor="middle" dominantBaseline="middle" fontSize={dim * 0.1} fontWeight="800" fill="#ffffff" stroke="#3559c7" strokeWidth={dim * 0.012} paintOrder="stroke fill">
              10
            </text>
          </g>

          <g>
            <path d={`M ${center - radius} ${center} A ${radius} ${radius} 0 0 1 ${center} ${center - radius}`} fill="none" stroke="#111111" strokeWidth={dim * 0.008} />
            <path d={`M ${center} ${center - radius} A ${radius} ${radius} 0 0 1 ${center + radius} ${center}`} fill="none" stroke="#111111" strokeWidth={dim * 0.008} />
            <path d={`M ${center + radius} ${center} A ${radius} ${radius} 0 0 1 ${center} ${center + radius}`} fill="none" stroke="#111111" strokeWidth={dim * 0.008} />
            <path d={`M ${center} ${center + radius} A ${radius} ${radius} 0 0 1 ${center - radius} ${center}`} fill="none" stroke="#111111" strokeWidth={dim * 0.008} />
          </g>

          <g>
            <path d={`M ${center - radius} ${center - radius} Q ${center - radius * 0.82} ${center - radius * 0.18} ${center - innerRadius} ${center - innerRadius} Q ${center - innerRadius * 0.18} ${center - radius * 0.82} ${center} ${center - radius}`} fill="none" stroke="#2e8b57" strokeWidth={dim * 0.018} strokeLinecap="round" />
            <path d={`M ${center + radius} ${center - radius} Q ${center + radius * 0.18} ${center - radius * 0.82} ${center + innerRadius} ${center - innerRadius} Q ${center + radius * 0.82} ${center - radius * 0.18} ${center} ${center - radius}`} fill="none" stroke="#e53935" strokeWidth={dim * 0.018} strokeLinecap="round" />
            <path d={`M ${center + radius} ${center + radius} Q ${center + radius * 0.82} ${center + radius * 0.18} ${center + innerRadius} ${center + innerRadius} Q ${center + innerRadius * 0.18} ${center + radius * 0.82} ${center} ${center + radius}`} fill="none" stroke="#3559c7" strokeWidth={dim * 0.018} strokeLinecap="round" />
            <path d={`M ${center - radius} ${center + radius} Q ${center - radius * 0.18} ${center + radius * 0.82} ${center - innerRadius} ${center + innerRadius} Q ${center - radius * 0.82} ${center + radius * 0.18} ${center} ${center + radius}`} fill="none" stroke="#d28f07" strokeWidth={dim * 0.018} strokeLinecap="round" />
          </g>
        </svg>
      </div>
    );
  }
);

BaseTrueWheel.displayName = "BaseTrueWheel";
