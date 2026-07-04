import React from "react";
import SlideDocument from "../../presentation/slides/delivery-control-tower.mdx";
import { LayoutGrid, Panel, Quadrant, ComponentPreview } from "./primitives";

const mdxComponents = {
  LayoutGrid,
  Panel,
  Quadrant,
  ComponentPreview,
};

export default function DeliveryControlTowerSlideGenerated() {
  return <SlideDocument components={mdxComponents} />;
}
