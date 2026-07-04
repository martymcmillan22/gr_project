/**
 * Card Component
 * Container component using Tailwind CSS + design tokens
 */

import React from "react";
import { cn } from "./styles";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  padding?: "xs" | "sm" | "md" | "lg" | "xl";
  shadow?: "sm" | "md" | "lg" | "xl";
}

const paddingClasses = {
  xs: "p-xs",
  sm: "p-sm",
  md: "p-md",
  lg: "p-lg",
  xl: "p-xl",
};

const shadowClasses = {
  sm: "shadow-sm",
  md: "shadow-md",
  lg: "shadow-lg",
  xl: "shadow-xl",
};

const baseClasses = "rounded-lg border border-neutral-200 bg-neutral-050";

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ padding = "lg", shadow = "md", className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(baseClasses, paddingClasses[padding], shadowClasses[shadow], className)}
        {...props}
      />
    );
  }
);

Card.displayName = "Card";
