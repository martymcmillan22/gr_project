import React from "react";
import SlideDocument from "../../presentation/slides/client-health-storyboard.mdx";
import { LayoutGrid, Panel, Quadrant, ComponentPreview } from "./primitives";

const mdxComponents = {
  LayoutGrid,
  Panel,
  Quadrant,
  ComponentPreview,
};

export default function ClientHealthStoryboardSlideGenerated() {
  return <SlideDocument components={mdxComponents} />;
}
