import React from "react";
import SlideDocument from "../../slides/ui_blueprint_standard.mdx";
import { LayoutGrid, Panel, Quadrant, ComponentPreview } from "./primitives";

const mdxComponents = {
  LayoutGrid,
  Panel,
  Quadrant,
  ComponentPreview,
};

export default function UiBlueprintStandardSlideGenerated() {
  return <SlideDocument components={mdxComponents} />;
}
