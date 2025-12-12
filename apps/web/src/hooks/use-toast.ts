"use client"

/**
 * @fileoverview Custom toast notification hook and utilities.
 *
 * This module provides a complete toast notification system inspired by react-hot-toast,
 * featuring a reducer-based state management pattern with support for multiple toast types,
 * automatic dismissal, and manual control over toast lifecycle.
 *
 * @module use-toast
 * @see {@link https://react-hot-toast.com/} Inspired by react-hot-toast
 */

import * as React from "react"

import type {
  ToastActionElement,
  ToastProps,
} from "@/components/ui/toast"

/**
 * Maximum number of toasts that can be displayed simultaneously.
 * When exceeded, older toasts are automatically removed.
 * @constant {number}
 */
const TOAST_LIMIT = 1

/**
 * Delay in milliseconds before a dismissed toast is removed from the DOM.
 * Set to a high value to allow for exit animations.
 * @constant {number}
 */
const TOAST_REMOVE_DELAY = 1000000

/**
 * Extended toast properties including identification and optional content.
 * Combines base ToastProps with additional fields for toast management.
 *
 * @typedef {Object} ToasterToast
 * @property {string} id - Unique identifier for the toast
 * @property {React.ReactNode} [title] - Optional title displayed in the toast header
 * @property {React.ReactNode} [description] - Optional description/body content
 * @property {ToastActionElement} [action] - Optional action button/element
 */
type ToasterToast = ToastProps & {
  id: string
  title?: React.ReactNode
  description?: React.ReactNode
  action?: ToastActionElement
}

/**
 * Redux-style action types for toast state management.
 * Used by the reducer to handle different toast operations.
 * @constant
 */
const actionTypes = {
  ADD_TOAST: "ADD_TOAST",
  UPDATE_TOAST: "UPDATE_TOAST",
  DISMISS_TOAST: "DISMISS_TOAST",
  REMOVE_TOAST: "REMOVE_TOAST",
} as const

/**
 * Counter for generating unique toast IDs.
 * Wraps around at MAX_SAFE_INTEGER to prevent overflow.
 * @private
 */
let count = 0

/**
 * Generates a unique identifier for each toast notification.
 *
 * Uses a simple incrementing counter that wraps around at Number.MAX_SAFE_INTEGER
 * to ensure uniqueness within a single session while preventing integer overflow.
 *
 * @returns {string} A unique string identifier for the toast
 *
 * @example
 * const id1 = genId(); // "1"
 * const id2 = genId(); // "2"
 * // ... continues incrementing
 *
 * @private
 */
function genId() {
  count = (count + 1) % Number.MAX_SAFE_INTEGER
  return count.toString()
}

type ActionType = typeof actionTypes

type Action =
  | {
      type: ActionType["ADD_TOAST"]
      toast: ToasterToast
    }
  | {
      type: ActionType["UPDATE_TOAST"]
      toast: Partial<ToasterToast>
    }
  | {
      type: ActionType["DISMISS_TOAST"]
      toastId?: ToasterToast["id"]
    }
  | {
      type: ActionType["REMOVE_TOAST"]
      toastId?: ToasterToast["id"]
    }

interface State {
  toasts: ToasterToast[]
}

/**
 * Map storing timeout handles for pending toast removals.
 * Used to track and manage delayed DOM removal of dismissed toasts.
 * @private
 */
const toastTimeouts = new Map<string, ReturnType<typeof setTimeout>>()

/**
 * Schedules a toast for removal from the DOM after TOAST_REMOVE_DELAY.
 *
 * This function queues a toast for delayed removal, allowing time for exit
 * animations to complete before the toast is actually removed from state.
 * If a toast is already queued for removal, subsequent calls are ignored.
 *
 * @param toastId - The unique identifier of the toast to schedule for removal
 *
 * @example
 * // Schedule toast "toast-123" for removal
 * addToRemoveQueue("toast-123");
 * // After TOAST_REMOVE_DELAY ms, the toast will be removed from state
 *
 * @private
 */
const addToRemoveQueue = (toastId: string) => {
  if (toastTimeouts.has(toastId)) {
    return
  }

  const timeout = setTimeout(() => {
    toastTimeouts.delete(toastId)
    dispatch({
      type: "REMOVE_TOAST",
      toastId: toastId,
    })
  }, TOAST_REMOVE_DELAY)

  toastTimeouts.set(toastId, timeout)
}

/**
 * Redux-style reducer for managing toast notification state.
 *
 * Handles four action types:
 * - ADD_TOAST: Adds a new toast, enforcing TOAST_LIMIT
 * - UPDATE_TOAST: Updates an existing toast's properties
 * - DISMISS_TOAST: Marks toast(s) as closed and queues for removal
 * - REMOVE_TOAST: Removes toast(s) from state completely
 *
 * @param state - Current toast state containing array of toasts
 * @param action - Action object describing the state change
 * @returns New state with the action applied
 *
 * @example
 * const newState = reducer(currentState, {
 *   type: "ADD_TOAST",
 *   toast: { id: "1", title: "Hello", open: true }
 * });
 *
 * @example
 * const dismissedState = reducer(currentState, {
 *   type: "DISMISS_TOAST",
 *   toastId: "1" // or undefined to dismiss all
 * });
 */
export const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case "ADD_TOAST":
      return {
        ...state,
        toasts: [action.toast, ...state.toasts].slice(0, TOAST_LIMIT),
      }

    case "UPDATE_TOAST":
      return {
        ...state,
        toasts: state.toasts.map((t) =>
          t.id === action.toast.id ? { ...t, ...action.toast } : t
        ),
      }

    case "DISMISS_TOAST": {
      const { toastId } = action

      // ! Side effects ! - This could be extracted into a dismissToast() action,
      // but I'll keep it here for simplicity
      if (toastId) {
        addToRemoveQueue(toastId)
      } else {
        state.toasts.forEach((toast) => {
          addToRemoveQueue(toast.id)
        })
      }

      return {
        ...state,
        toasts: state.toasts.map((t) =>
          t.id === toastId || toastId === undefined
            ? {
                ...t,
                open: false,
              }
            : t
        ),
      }
    }
    case "REMOVE_TOAST":
      if (action.toastId === undefined) {
        return {
          ...state,
          toasts: [],
        }
      }
      return {
        ...state,
        toasts: state.toasts.filter((t) => t.id !== action.toastId),
      }
  }
}

/**
 * Array of subscriber functions that receive state updates.
 * Components using useToast hook register listeners here.
 * @private
 */
const listeners: Array<(state: State) => void> = []

/**
 * In-memory state store for toast notifications.
 * Persists across component re-renders and is shared globally.
 * @private
 */
let memoryState: State = { toasts: [] }

/**
 * Dispatches an action to update toast state and notify all listeners.
 *
 * This function serves as the central state update mechanism, applying
 * the action through the reducer and then notifying all registered
 * listener functions (typically React setState functions).
 *
 * @param action - The action to dispatch
 *
 * @example
 * dispatch({ type: "ADD_TOAST", toast: newToast });
 * dispatch({ type: "DISMISS_TOAST", toastId: "toast-123" });
 *
 * @private
 */
function dispatch(action: Action) {
  memoryState = reducer(memoryState, action)
  listeners.forEach((listener) => {
    listener(memoryState)
  })
}

/**
 * Toast creation options type.
 * Includes all ToasterToast properties except the auto-generated id.
 */
type Toast = Omit<ToasterToast, "id">

/**
 * Creates and displays a new toast notification.
 *
 * This is the primary function for showing toast notifications in the application.
 * It generates a unique ID, dispatches the ADD_TOAST action, and returns
 * control functions for updating or dismissing the toast.
 *
 * @param props - Toast configuration options (title, description, variant, etc.)
 * @returns Object containing the toast id and control functions
 *
 * @example
 * // Simple toast
 * toast({ title: "Success!", description: "Your changes were saved." });
 *
 * @example
 * // With action button
 * toast({
 *   title: "Undo available",
 *   action: <ToastAction onClick={handleUndo}>Undo</ToastAction>
 * });
 *
 * @example
 * // Using returned controls
 * const { id, dismiss, update } = toast({ title: "Loading..." });
 * // Later...
 * update({ title: "Complete!", description: "All done." });
 * // Or...
 * dismiss();
 */
function toast({ ...props }: Toast) {
  const id = genId()

  const update = (props: ToasterToast) =>
    dispatch({
      type: "UPDATE_TOAST",
      toast: { ...props, id },
    })
  const dismiss = () => dispatch({ type: "DISMISS_TOAST", toastId: id })

  dispatch({
    type: "ADD_TOAST",
    toast: {
      ...props,
      id,
      open: true,
      onOpenChange: (open) => {
        if (!open) dismiss()
      },
    },
  })

  return {
    id: id,
    dismiss,
    update,
  }
}

/**
 * React hook for accessing and managing toast notifications.
 *
 * This hook provides access to the current toast state and functions
 * for creating and dismissing toasts. It automatically subscribes to
 * state updates and cleans up on unmount.
 *
 * @returns Object containing:
 *   - toasts: Array of current toast objects
 *   - toast: Function to create a new toast
 *   - dismiss: Function to dismiss a specific toast or all toasts
 *
 * @example
 * function MyComponent() {
 *   const { toast, dismiss, toasts } = useToast();
 *
 *   const handleClick = () => {
 *     toast({
 *       title: "Action completed",
 *       description: "Your request was successful",
 *     });
 *   };
 *
 *   const dismissAll = () => dismiss(); // No id = dismiss all
 *
 *   return (
 *     <div>
 *       <button onClick={handleClick}>Show Toast</button>
 *       <span>Active toasts: {toasts.length}</span>
 *     </div>
 *   );
 * }
 *
 * @example
 * // Dismiss a specific toast
 * const { dismiss } = useToast();
 * dismiss("toast-123");
 *
 * @example
 * // Dismiss all toasts
 * const { dismiss } = useToast();
 * dismiss();
 */
function useToast() {
  const [state, setState] = React.useState<State>(memoryState)

  React.useEffect(() => {
    listeners.push(setState)
    return () => {
      const index = listeners.indexOf(setState)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }, [state])

  return {
    ...state,
    toast,
    dismiss: (toastId?: string) => dispatch({ type: "DISMISS_TOAST", toastId }),
  }
}

export { useToast, toast }
