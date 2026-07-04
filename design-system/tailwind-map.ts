/**
 * Tailwind Config Token Mapping
 * Maps design-system tokens to Tailwind CSS classes
 */

import { tokens } from "./tokens";

export const tailwindConfig = {
  theme: {
    extend: {
      colors: {
        primary: tokens.colors.primary,
        neutral: tokens.colors.neutral,
        success: tokens.colors.success,
        warning: tokens.colors.warning,
        error: tokens.colors.error,
      },
      spacing: tokens.spacing,
      borderRadius: tokens.borderRadius,
      boxShadow: tokens.shadows,
      fontSize: {
        "heading-h1": [
          tokens.typography.heading.h1.fontSize,
          { fontWeight: tokens.typography.heading.h1.fontWeight, lineHeight: tokens.typography.heading.h1.lineHeight },
        ],
        "heading-h2": [
          tokens.typography.heading.h2.fontSize,
          { fontWeight: tokens.typography.heading.h2.fontWeight, lineHeight: tokens.typography.heading.h2.lineHeight },
        ],
        "heading-h3": [
          tokens.typography.heading.h3.fontSize,
          { fontWeight: tokens.typography.heading.h3.fontWeight, lineHeight: tokens.typography.heading.h3.lineHeight },
        ],
        "body-base": [
          tokens.typography.body.base.fontSize,
          { fontWeight: tokens.typography.body.base.fontWeight, lineHeight: tokens.typography.body.base.lineHeight },
        ],
        "body-sm": [
          tokens.typography.body.sm.fontSize,
          { fontWeight: tokens.typography.body.sm.fontWeight, lineHeight: tokens.typography.body.sm.lineHeight },
        ],
      },
    },
  },
};

/**
 * Export theme for use in tailwind.config.js
 */
export const theme = tailwindConfig.theme;
