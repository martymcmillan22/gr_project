import React from "react";
import { cn } from "../ui/styles";
import { tokens } from "@/design-system/tokens";

export interface AstrologyWheelProps {
  className?: string;
  size?: number;
  label?: string;
}

export const AstrologyWheel = React.forwardRef<HTMLDivElement, AstrologyWheelProps>(
  ({ className, size = 450, label = "Astrology wheel diagram" }, ref) => {
    const center = size / 2;
    const outerRadius = 200;
    const innerRadius = 110;

    const quadrant = {
      green: tokens.colors.green["500"],
      red: tokens.colors.pink["500"],
      blue: tokens.colors.primary["500"],
      yellow: tokens.colors.orange["500"],
      outline: tokens.colors.neutral["900"],
      background: "#ffffff",
    } as const;

    return (
      <div ref={ref} className={cn("flex w-full items-center justify-center", className)}>
        <div className="relative inline-block">
          <svg
            width={size}
            height={size}
            viewBox={`0 0 ${size} ${size}`}
            className="h-auto w-full max-w-2xl"
            role="img"
            aria-label={label}
          >
            <title>{label}</title>
            <desc>
              Circular astrology chart with quadrants, house numbers, and concentric rings.
            </desc>

            <circle cx={center} cy={center} r={outerRadius} fill={quadrant.background} />
            <circle cx={center} cy={center} r={innerRadius} fill={quadrant.background} />

            <line
              x1={center}
              y1={center - innerRadius}
              x2={center}
              y2={center - outerRadius}
              stroke={quadrant.green}
              strokeWidth="3"
            />
            <path
              d={`M ${center - outerRadius} ${center} Q ${center - 140} ${center - 140} ${center} ${center - outerRadius}`}
              stroke={quadrant.green}
              strokeWidth="3"
              fill="none"
            />
            <path
              d={`M ${center - innerRadius} ${center} Q ${center - 78} ${center - 78} ${center} ${center - innerRadius}`}
              stroke={quadrant.green}
              strokeWidth="2"
              fill="none"
            />

            <line
              x1={center}
              y1={center - innerRadius}
              x2={center}
              y2={center - outerRadius}
              stroke={quadrant.red}
              strokeWidth="3"
            />
            <path
              d={`M ${center} ${center - outerRadius} Q ${center + 140} ${center - 140} ${center + outerRadius} ${center}`}
              stroke={quadrant.red}
              strokeWidth="3"
              fill="none"
            />
            <path
              d={`M ${center} ${center - innerRadius} Q ${center + 78} ${center - 78} ${center + innerRadius} ${center}`}
              stroke={quadrant.red}
              strokeWidth="2"
              fill="none"
            />

            <line
              x1={center}
              y1={center + innerRadius}
              x2={center}
              y2={center + outerRadius}
              stroke={quadrant.blue}
              strokeWidth="3"
            />
            <path
              d={`M ${center + outerRadius} ${center} Q ${center + 140} ${center + 140} ${center} ${center + outerRadius}`}
              stroke={quadrant.blue}
              strokeWidth="3"
              fill="none"
            />
            <path
              d={`M ${center + innerRadius} ${center} Q ${center + 78} ${center + 78} ${center} ${center + innerRadius}`}
              stroke={quadrant.blue}
              strokeWidth="2"
              fill="none"
            />

            <line
              x1={center}
              y1={center + innerRadius}
              x2={center}
              y2={center + outerRadius}
              stroke={quadrant.yellow}
              strokeWidth="3"
            />
            <path
              d={`M ${center} ${center + outerRadius} Q ${center - 140} ${center + 140} ${center - outerRadius} ${center}`}
              stroke={quadrant.yellow}
              strokeWidth="3"
              fill="none"
            />
            <path
              d={`M ${center} ${center + innerRadius} Q ${center - 78} ${center + 78} ${center - innerRadius} ${center}`}
              stroke={quadrant.yellow}
              strokeWidth="2"
              fill="none"
            />

            <line
              x1={center}
              y1={center - innerRadius}
              x2={center}
              y2={center + innerRadius}
              stroke={quadrant.outline}
              strokeWidth="2.5"
            />
            <line
              x1={center - innerRadius}
              y1={center}
              x2={center + innerRadius}
              y2={center}
              stroke={quadrant.outline}
              strokeWidth="2.5"
            />

            <circle
              cx={center}
              cy={center}
              r={outerRadius}
              fill="none"
              stroke={quadrant.outline}
              strokeWidth="2.5"
            />
            <circle
              cx={center}
              cy={center}
              r={innerRadius}
              fill="none"
              stroke={quadrant.outline}
              strokeWidth="2.5"
            />

            <text
              x={center - 60}
              y={center - 60}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="32"
              fontWeight="700"
              fill={quadrant.green}
            >
              12
            </text>
            <text
              x={center - 85}
              y={center - 10}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="28"
              fontWeight="700"
              fill={quadrant.green}
            >
              4
            </text>
            <text
              x={center - 25}
              y={center + 5}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="32"
              fontWeight="700"
              fill={quadrant.green}
            >
              8
            </text>

            <text
              x={center + 60}
              y={center - 60}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="32"
              fontWeight="700"
              fill={quadrant.red}
            >
              1
            </text>
            <text
              x={center + 30}
              y={center + 5}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="32"
              fontWeight="700"
              fill={quadrant.red}
            >
              5
            </text>
            <text
              x={center + 85}
              y={center - 10}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="28"
              fontWeight="700"
              fill={quadrant.red}
            >
              9
            </text>

            <text
              x={center - 75}
              y={center + 55}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="28"
              fontWeight="700"
              fill={quadrant.yellow}
            >
              11
            </text>
            <text
              x={center - 25}
              y={center + 35}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="32"
              fontWeight="700"
              fill={quadrant.yellow}
            >
              7
            </text>
            <text
              x={center - 25}
              y={center + 85}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="32"
              fontWeight="700"
              fill={quadrant.yellow}
            >
              3
            </text>

            <text
              x={center + 30}
              y={center + 35}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="32"
              fontWeight="700"
              fill={quadrant.blue}
            >
              6
            </text>
            <text
              x={center + 75}
              y={center + 55}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="28"
              fontWeight="700"
              fill={quadrant.blue}
            >
              2
            </text>
            <text
              x={center + 30}
              y={center + 85}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="32"
              fontWeight="700"
              fill={quadrant.blue}
            >
              10
            </text>

            <circle cx={center} cy={center} r="5" fill={quadrant.outline} />
          </svg>

          <div className="absolute -top-24 left-0 right-0 flex justify-center">
            <div className="text-5xl font-black tracking-[0.12em]">
              <span className="text-primary-400">B</span>
              <span className="text-pink-500">A</span>
              <span className="text-green-500">S</span>
              <span className="text-orange-500">T</span>
              <span className="text-pink-500">E</span>
              <span className="text-primary-400">T</span>
              <span className="text-green-500">R</span>
              <span className="text-orange-500">U</span>
              <span className="text-pink-500">E</span>
            </div>
          </div>
        </div>
      </div>
    );
  }
);

AstrologyWheel.displayName = "AstrologyWheel";
