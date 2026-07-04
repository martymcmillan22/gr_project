import { useEffect, useState } from "react";

import { quadrantLinkConfig } from "./quadrantLinksConfig";

const quadrantSlots = Array.from({ length: 12 }, (_value, index) => index + 1);
const quadrantPositions = {
  1: { left: "59.973%", top: "23.585%" },
  2: { left: "62.668%", top: "84.232%" },
  3: { left: "43.801%", top: "84.232%" },
  4: { left: "17.520%", top: "45.148%" },
  5: { left: "59.973%", top: "45.148%" },
  6: { left: "61.321%", top: "59.973%" },
  7: { left: "42.453%", top: "61.321%" },
  8: { left: "45.148%", top: "44.474%" },
  9: { left: "77.493%", top: "45.148%" },
  10: { left: "78.841%", top: "59.973%" },
  11: { left: "19.542%", top: "61.995%" },
  12: { left: "40.431%", top: "23.585%" },
};

export function getCurrentHour() {
  const hour = new Date().getHours() % 12;
  return hour === 0 ? 12 : hour;
}

export function isPM() {
  return new Date().getHours() >= 12;
}

export function resolveDomain(hour, isPm) {
  const normalizedHour = ((Number(hour) - 1) % 12 + 12) % 12 + 1;
  const branch = isPm ? quadrantLinkConfig.pmDomains : quadrantLinkConfig.amDomains;
  const target = branch[normalizedHour];
  if (!target) {
    throw new Error(`Missing quadrant link target for hour ${normalizedHour} (${isPm ? "PM" : "AM"})`);
  }
  const namespace = isPm ? "domain" : "center";
  return `/${namespace}/grid/${target.slug}/`;
}

export function getLinkForNumber(number) {
  return resolveDomain(number, isPM());
}

function getQuadrantBasePath() {
  return import.meta.env.DEV ? "/quadrant/" : "/contracts/quadrant/";
}

function getQuadrantHeatmapPath() {
  return `${getQuadrantBasePath()}heatmap/`;
}

function getQuadrantOverlayPath() {
  return `${getQuadrantBasePath()}overlay/`;
}

export async function goToQuadrant({
  fetchImpl = globalThis.fetch,
  endpoint = getQuadrantBasePath(),
  navigate = (url) => {
    if (typeof window !== "undefined") {
      window.location.assign(url);
    }
  },
} = {}) {
  const response = await fetchImpl(endpoint, {
    method: "GET",
    redirect: "follow",
    credentials: "include",
  });
  if (response.redirected) {
    const resolvedUrl = response.url;
    navigate(resolvedUrl);
    return resolvedUrl;
  }

  const data = await response.json();
  const resolvedUrl = data?.url || "/quadrant/";
  navigate(resolvedUrl);
  return resolvedUrl;
}

function QuadrantHeatmap() {
  const [data, setData] = useState({ am: {}, pm: {} });
  const hours = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];

  useEffect(() => {
    let active = true;
    fetch(getQuadrantHeatmapPath(), {
      method: "GET",
      credentials: "include",
    })
      .then((response) => response.json())
      .then((payload) => {
        if (active) {
          setData(payload);
        }
      })
      .catch((error) => {
        console.error("Heatmap fetch failed:", error);
      });
    return () => {
      active = false;
    };
  }, []);

  const cellClass = (count) => {
    if (count === 0) return "heatmap-cell level-0";
    if (count < 5) return "heatmap-cell level-1";
    if (count < 15) return "heatmap-cell level-2";
    return "heatmap-cell level-3";
  };

  return (
    <div className="quadrant-heatmap" aria-label="Quadrant usage heatmap">
      <div className="heatmap-row">
        {hours.map((hour) => {
          const count = data.am?.[String(hour)] || 0;
          return (
            <div key={`am-${hour}`} className={cellClass(count)} title={`AM ${hour}: ${count}`} aria-label={`AM ${hour}: ${count}`} />
          );
        })}
      </div>
      <div className="heatmap-row">
        {hours.map((hour) => {
          const count = data.pm?.[String(hour)] || 0;
          return (
            <div key={`pm-${hour}`} className={cellClass(count)} title={`PM ${hour}: ${count}`} aria-label={`PM ${hour}: ${count}`} />
          );
        })}
      </div>
    </div>
  );
}

export default function QuadrantSandbox({ goToQuadrantFn = goToQuadrant } = {}) {
  const currentHour = getCurrentHour();
  const currentIsPm = isPM();
  const [overlayData, setOverlayData] = useState({ slots: [] });
  const twistWheelImageSrc = import.meta.env.DEV
    ? "/images/Twist.png"
    : "/static/images/Twist.png";

  useEffect(() => {
    let active = true;
    fetch(getQuadrantOverlayPath(), {
      method: "GET",
      credentials: "include",
    })
      .then((response) => response.json())
      .then((payload) => {
        if (active) {
          setOverlayData(payload || { slots: [] });
        }
      })
      .catch((error) => {
        console.error("Overlay fetch failed:", error);
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <section className="twist-visual quadrant-sandbox" aria-label="Quadrant sandbox with dynamic number links">
      <div className="twist-forest-header quadrant-sandbox-header" aria-label="Quadrant sandbox header">
        <div className="twist-forest-control twist-forest-control-left">
          <span>Mode</span>
          <strong>{currentIsPm ? "PM" : "AM"}</strong>
        </div>

        <span className="twist-forest-title">Quadrant Sandbox</span>

        <div className="twist-forest-control twist-forest-control-right">
          <span>Hour</span>
          <strong>{currentHour}</strong>
        </div>
      </div>

      <div className="twist-assistant-center quadrant-sandbox-image-wrap">
        <img src={twistWheelImageSrc} alt="Twist visual" />
      </div>

      {overlayData.inversion?.is_active ? (
        <p className="quadrant-inversion-banner" role="status" aria-live="polite">
          Inversion hinge active: {overlayData.inversion.source.mode.toUpperCase()} {overlayData.inversion.source.hour} -> {overlayData.inversion.target.mode.toUpperCase()} {overlayData.inversion.target.hour}
        </p>
      ) : null}
    </section>
  );
}
