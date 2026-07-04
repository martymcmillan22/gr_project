import React from "react";
import SlideDocument from "../../presentation/slides/customer-journey-canvas.mdx";
import { LayoutGrid, Panel, Quadrant, ComponentPreview } from "./primitives";

const mdxComponents = {
  LayoutGrid,
  Panel,
  Quadrant,
  ComponentPreview,
};

export default function CustomerJourneyCanvasSlideGenerated() {
  return <SlideDocument components={mdxComponents} />;
}
