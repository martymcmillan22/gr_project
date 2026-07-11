/**
 * Button Component
 * Radix UI primitive + Tailwind CSS
 * Token-driven styling
 */

import React from "react";
import { cn } from "./styles";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
  asChild?: boolean;
}

const variantClasses = {
  primary:
    "bg-primary-600 text-white hover:bg-primary-700 active:bg-primary-800 focus:ring-primary-500 disabled:bg-neutral-500",
  secondary:
    "bg-neutral-200 text-neutral-900 hover:bg-neutral-300 active:bg-neutral-400 focus:ring-neutral-400 disabled:bg-neutral-300",
  ghost:
    "bg-transparent text-primary-600 hover:bg-primary-50 active:bg-primary-100 focus:ring-primary-300 disabled:text-neutral-400",
};

const sizeClasses = {
  sm: "px-md py-sm text-body-sm",
  md: "px-lg py-md text-body-base",
  lg: "px-xl py-lg text-body-base",
};

const baseClasses =
  "inline-flex items-center justify-center rounded-md border border-transparent font-medium transition-all duration-200 cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60";

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      className,
      disabled = false,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled}
        className={cn(
          baseClasses,
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        {...props}
      />
    );
  }
);

Button.displayName = "Button";
