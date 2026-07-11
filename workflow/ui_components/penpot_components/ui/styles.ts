/**
 * Class name utilities for consistent component styling
 */

import clsx, { type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind classes safely, removing conflicts
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Component size and variant maps using Tailwind classes
 */
export const buttonVariants = {
  primary: "bg-primary-600 text-white hover:bg-primary-700 active:bg-primary-800 disabled:bg-neutral-500 disabled:opacity-50",
  secondary: "bg-neutral-200 text-neutral-900 hover:bg-neutral-300 active:bg-neutral-400 disabled:opacity-50",
  ghost: "bg-transparent text-primary-600 hover:bg-primary-50 active:bg-primary-100 disabled:opacity-50",
};

export const buttonSizes = {
  sm: "px-md py-sm text-body-sm",
  md: "px-lg py-md text-body-base",
  lg: "px-xl py-lg text-body-base",
};

export const baseButtonStyles = "inline-flex items-center justify-center rounded-md border border-transparent font-medium transition-colors duration-200 cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:cursor-not-allowed";

export const cardStyles = "rounded-lg border border-neutral-200 bg-neutral--050 shadow-md";

export const headerStyles = "bg-primary-600 text-white border-b-4 border-primary-700";
