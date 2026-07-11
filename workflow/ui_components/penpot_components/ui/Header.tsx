/**
 * Header Component
 * Top-level navigation and branding component
 * Tailwind CSS + Radix UI
 */

import React from "react";
import { cn } from "./styles";

export interface HeaderProps extends React.HTMLAttributes<HTMLElement> {
  title: string;
  subtitle?: string;
}

const baseClasses = "bg-primary-600 text-white border-b-4 border-primary-700 px-xl py-lg";
const titleClasses = "text-heading-h2 font-bold m-0 mb-sm";
const subtitleClasses = "text-body-base m-0 opacity-90";

export const Header = React.forwardRef<HTMLElement, HeaderProps>(
  ({ title, subtitle, className, ...props }, ref) => {
    return (
      <header ref={ref} className={cn(baseClasses, className)} {...props}>
        <h1 className={titleClasses}>{title}</h1>
        {subtitle && <p className={subtitleClasses}>{subtitle}</p>}
      </header>
    );
  }
);

Header.displayName = "Header";

