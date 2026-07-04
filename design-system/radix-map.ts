/**
 * Radix UI Token Mapping
 * Maps design-system tokens to Radix UI primitive variables
 */

import { tokens } from "./tokens";

export const radixTokenMap = {
  // Color palette for Radix accent scale
  accentScale: {
    1: tokens.colors.primary["50"],
    2: tokens.colors.primary["100"],
    3: tokens.colors.primary["200"],
    4: tokens.colors.primary["300"],
    5: tokens.colors.primary["400"],
    6: tokens.colors.primary["500"],
    7: tokens.colors.primary["600"],
    8: tokens.colors.primary["700"],
    9: tokens.colors.primary["800"],
    10: tokens.colors.primary["900"],
  },

  // Neutral scale for grays
  neutralScale: {
    1: tokens.colors.neutral["50"],
    2: tokens.colors.neutral["100"],
    3: tokens.colors.neutral["200"],
    4: tokens.colors.neutral["300"],
    5: tokens.colors.neutral["400"],
    6: tokens.colors.neutral["500"],
    7: tokens.colors.neutral["600"],
    8: tokens.colors.neutral["700"],
    9: tokens.colors.neutral["800"],
    10: tokens.colors.neutral["900"],
  },

  // Semantic colors
  successColor: tokens.colors.success,
  warningColor: tokens.colors.warning,
  errorColor: tokens.colors.error,

  // Spacing
  spacing: tokens.spacing,

  // Border radius
  borderRadius: tokens.borderRadius,

  // Shadows
  shadows: tokens.shadows,
};

/**
 * Radix style config - use with Radix theme provider
 */
export const radixStyleConfig = {
  accentColor: "blue",
  grayColor: "slate",
  radius: "medium",
  scaling: "100%",
};
