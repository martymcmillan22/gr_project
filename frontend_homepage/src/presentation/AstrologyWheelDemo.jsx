const TOKENS = {
  green: "#4d9963",
  red: "#e84fa9",
  blue: "#087eb4",
  yellow: "#e96000",
  outline: "#222931",
};

function AstrologyWheelGraphic() {
  const size = 320;
  const center = size / 2;
  const outerRadius = 142;
  const innerRadius = 78;

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className="astrology-demo-wheel"
      role="img"
      aria-label="Astrology wheel preview"
    >
      <title>Astrology wheel preview</title>
      <desc>Compact astrology wheel demo showing the four colored quadrants and house numbers.</desc>

      <circle cx={center} cy={center} r={outerRadius} fill="#ffffff" />
      <circle cx={center} cy={center} r={innerRadius} fill="#ffffff" />

      <line x1={center} y1={center - innerRadius} x2={center} y2={center - outerRadius} stroke={TOKENS.green} strokeWidth="3" />
      <path d={`M ${center - outerRadius} ${center} Q ${center - 100} ${center - 100} ${center} ${center - outerRadius}`} stroke={TOKENS.green} strokeWidth="3" fill="none" />
      <path d={`M ${center - innerRadius} ${center} Q ${center - 54} ${center - 54} ${center} ${center - innerRadius}`} stroke={TOKENS.green} strokeWidth="2" fill="none" />

      <line x1={center} y1={center - innerRadius} x2={center} y2={center - outerRadius} stroke={TOKENS.red} strokeWidth="3" />
      <path d={`M ${center} ${center - outerRadius} Q ${center + 100} ${center - 100} ${center + outerRadius} ${center}`} stroke={TOKENS.red} strokeWidth="3" fill="none" />
      <path d={`M ${center} ${center - innerRadius} Q ${center + 54} ${center - 54} ${center + innerRadius} ${center}`} stroke={TOKENS.red} strokeWidth="2" fill="none" />

      <line x1={center} y1={center + innerRadius} x2={center} y2={center + outerRadius} stroke={TOKENS.blue} strokeWidth="3" />
      <path d={`M ${center + outerRadius} ${center} Q ${center + 100} ${center + 100} ${center} ${center + outerRadius}`} stroke={TOKENS.blue} strokeWidth="3" fill="none" />
      <path d={`M ${center + innerRadius} ${center} Q ${center + 54} ${center + 54} ${center} ${center + innerRadius}`} stroke={TOKENS.blue} strokeWidth="2" fill="none" />

      <line x1={center} y1={center + innerRadius} x2={center} y2={center + outerRadius} stroke={TOKENS.yellow} strokeWidth="3" />
      <path d={`M ${center} ${center + outerRadius} Q ${center - 100} ${center + 100} ${center - outerRadius} ${center}`} stroke={TOKENS.yellow} strokeWidth="3" fill="none" />
      <path d={`M ${center} ${center + innerRadius} Q ${center - 54} ${center + 54} ${center - innerRadius} ${center}`} stroke={TOKENS.yellow} strokeWidth="2" fill="none" />

      <line x1={center} y1={center - innerRadius} x2={center} y2={center + innerRadius} stroke={TOKENS.outline} strokeWidth="2.5" />
      <line x1={center - innerRadius} y1={center} x2={center + innerRadius} y2={center} stroke={TOKENS.outline} strokeWidth="2.5" />
      <circle cx={center} cy={center} r={outerRadius} fill="none" stroke={TOKENS.outline} strokeWidth="2.5" />
      <circle cx={center} cy={center} r={innerRadius} fill="none" stroke={TOKENS.outline} strokeWidth="2.5" />

      <text x={center - 42} y={center - 38} textAnchor="middle" dominantBaseline="middle" fontSize="24" fontWeight="700" fill={TOKENS.green}>12</text>
      <text x={center + 40} y={center - 38} textAnchor="middle" dominantBaseline="middle" fontSize="24" fontWeight="700" fill={TOKENS.red}>1</text>
      <text x={center - 44} y={center + 40} textAnchor="middle" dominantBaseline="middle" fontSize="24" fontWeight="700" fill={TOKENS.yellow}>11</text>
      <text x={center + 40} y={center + 40} textAnchor="middle" dominantBaseline="middle" fontSize="24" fontWeight="700" fill={TOKENS.blue}>6</text>

      <circle cx={center} cy={center} r="4" fill={TOKENS.outline} />
    </svg>
  );
}

export default function AstrologyWheelDemo() {
  return (
    <section className="panel astrology-demo">
      <div className="astrology-demo-copy">
        <p className="eyebrow">Component Demo</p>
        <h2>Astrology Wheel Preview</h2>
        <p className="status-line">
          A compact homepage demo of the refined wheel component, built to show the token colors and geometry in context.
        </p>

        <div className="astrology-demo-chips">
          <span>token colors</span>
          <span>svg geometry</span>
          <span>accessible label</span>
        </div>
      </div>

      <div className="astrology-demo-art">
        <AstrologyWheelGraphic />
      </div>
    </section>
  );
}