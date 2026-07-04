import React from "react";
import SlideDocument from "../../slides/risk-operations-matrix.mdx";
import { LayoutGrid, Panel, Quadrant, ComponentPreview } from "./primitives";

const mdxComponents = {
  LayoutGrid,
  Panel,
  Quadrant,
  ComponentPreview,
};

export default function RiskOperationsMatrixSlideGenerated() {
  return <SlideDocument components={mdxComponents} />;
}
