import anchor from "../anchors/bt_anchor.json";
import type { GeometryMode } from "../types";

export function getDefaultGeometryMode(): GeometryMode {
  return "architectural";
}

export function getTransitionMode(isLargeScreen: boolean): string {
  return isLargeScreen
    ? anchor.geometry.transitions.large_screens
    : anchor.geometry.transitions.small_screens;
}
