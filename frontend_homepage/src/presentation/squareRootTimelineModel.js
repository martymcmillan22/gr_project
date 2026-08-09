export const TIMELINE_PHASES = [
  { id: "phase_1", timelineLabel: "Ideas", cpwState: "Intent", family: "idea" },
  { id: "phase_2", timelineLabel: "Seeds", cpwState: "Formation", family: "seed" },
  { id: "phase_3", timelineLabel: "Projects", cpwState: "Execution", family: "project" },
  { id: "phase_4", timelineLabel: "MVP", cpwState: "Validation", family: "mvp" },
];

export const TEMPORAL_ALIGNMENTS = ["past", "present-past", "present-future", "future"];
export const CALCULUS_OPERATIONS = ["Integral", "Continuity", "Limit", "Derivative"];

const GROUP_CATALOG = [
  { subject: "Math", colorToken: "red", colorHex: "#E53935" },
  { subject: "Language", colorToken: "blue", colorHex: "#1E88E5" },
  { subject: "Arts", colorToken: "yellow", colorHex: "#FBC02D" },
  { subject: "Science", colorToken: "green", colorHex: "#43A047" },
  { subject: "General Information", colorToken: "purple", colorHex: "#8E24AA" },
  { subject: "Literature", colorToken: "teal", colorHex: "#00897B" },
  { subject: "Crafts", colorToken: "orange", colorHex: "#FB8C00" },
  { subject: "Technology", colorToken: "lime", colorHex: "#7CB342" },
  { subject: "History", colorToken: "red-purple", colorHex: "#C2185B" },
  { subject: "Geography", colorToken: "blue-teal", colorHex: "#00ACC1" },
  { subject: "Architecture", colorToken: "yellow-orange", colorHex: "#FFB300" },
  { subject: "Ecology", colorToken: "green-lime", colorHex: "#9CCC65" },
  { subject: "Philosophy", colorToken: "deep-crimson", colorHex: "#8E2430" },
  { subject: "Law & Governance", colorToken: "deep-indigo", colorHex: "#3949AB" },
  { subject: "Economics", colorToken: "gold-ochre", colorHex: "#B8860B" },
  { subject: "Systemics", colorToken: "deep-forest", colorHex: "#1B5E20" },
];

function slugify(value = "") {
  return String(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

const RAW_SQUARE_ROOT_TIMELINE_CELLS = GROUP_CATALOG.map((item, index) => {
  const latticeIndex = index + 1;
  const rowPhase = Math.floor(index / 4) + 1;
  const colSlot = (index % 4) + 1;
  const phase = TIMELINE_PHASES[rowPhase - 1] || TIMELINE_PHASES[0];
  const temporalAlignment = TEMPORAL_ALIGNMENTS[colSlot - 1];
  const calculusOperation = CALCULUS_OPERATIONS[colSlot - 1];
  const phaseSlug = slugify(phase.family || phase.timelineLabel || "timeline");
  const subjectSlug = slugify(item.subject || `group-${latticeIndex}`);

  return {
    latticeIndex,
    rowPhase,
    colSlot,
    timelineLabel: phase.timelineLabel,
    cpwState: phase.cpwState,
    family: phase.family,
    temporalAlignment,
    temporal_alignment: temporalAlignment,
    calculusOperation,
    calculus_operation: calculusOperation,
    presetId: `${phaseSlug}.${temporalAlignment.toLowerCase()}.${subjectSlug}`,
    mlasSubject: item.subject,
    mlasColorToken: item.colorToken,
    colorHex: item.colorHex,
    semanticIntentId: `intent_${String(latticeIndex).padStart(2, "0")}`,
  };
});

export const SQUARE_ROOT_TIMELINE_CELLS = RAW_SQUARE_ROOT_TIMELINE_CELLS.map((cell) => ({
  ...cell,
  links: {
    svemId: `svem-${cell.colSlot}`,
    cccpId: `cccp-${cell.latticeIndex}`,
    dchdId: `dchd-${cell.latticeIndex}`,
  },
}));

export function getCellsByPhase(phaseIndex) {
  return SQUARE_ROOT_TIMELINE_CELLS.filter((cell) => cell.rowPhase === phaseIndex).sort((a, b) => a.colSlot - b.colSlot);
}