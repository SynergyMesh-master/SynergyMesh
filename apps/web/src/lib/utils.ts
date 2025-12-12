import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Utility function for merging CSS class names with Tailwind CSS support.
 *
 * This function combines the power of `clsx` for conditional class name joining
 * with `tailwind-merge` for intelligent Tailwind CSS class merging that handles
 * conflicts (e.g., `px-2` and `px-4` will result in only `px-4`).
 *
 * @param inputs - Array of class values that can be strings, objects, arrays,
 *                 or any valid `clsx` input type. Supports conditional classes
 *                 through object syntax: `{ 'class-name': condition }`
 *
 * @returns A single merged class name string with Tailwind CSS conflicts resolved
 *
 * @example
 * // Basic usage with strings
 * cn('px-2 py-1', 'text-blue-500')
 * // Returns: 'px-2 py-1 text-blue-500'
 *
 * @example
 * // Conditional classes with objects
 * cn('base-class', { 'active': isActive, 'disabled': isDisabled })
 * // Returns: 'base-class active' (if isActive is true, isDisabled is false)
 *
 * @example
 * // Tailwind conflict resolution
 * cn('px-2 text-red-500', 'px-4 text-blue-500')
 * // Returns: 'px-4 text-blue-500' (later classes win in conflicts)
 *
 * @example
 * // With arrays and mixed inputs
 * cn(['flex', 'items-center'], { 'gap-2': hasGap }, className)
 * // Merges all inputs intelligently
 *
 * @see {@link https://github.com/lukeed/clsx} clsx documentation
 * @see {@link https://github.com/dcastil/tailwind-merge} tailwind-merge documentation
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
