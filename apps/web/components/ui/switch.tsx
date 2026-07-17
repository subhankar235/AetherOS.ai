"use client"

import { useState, useEffect } from "react"
import { cn } from "@/lib/utils"

function Switch({
  className,
  defaultChecked,
  checked: controlledChecked,
  disabled,
  ...props
}: {
  className?: string
  defaultChecked?: boolean
  checked?: boolean
  disabled?: boolean
} & Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "defaultChecked" | "checked" | "disabled">) {
  const [internalOn, setInternalOn] = useState(defaultChecked ?? false)
  const isControlled = controlledChecked !== undefined
  const on = isControlled ? controlledChecked : internalOn

  useEffect(() => {
    if (isControlled) {
      setInternalOn(controlledChecked!)
    }
  }, [controlledChecked, isControlled])

  return (
    <button
      role="switch"
      aria-checked={on}
      disabled={disabled}
      onClick={() => { if (!isControlled) setInternalOn((v) => !v) }}
      className={cn(
        "peer inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50",
        on ? "bg-primary" : "bg-input",
        className
      )}
      {...props}
    >
      <span
        className={cn(
          "pointer-events-none block h-4 w-4 rounded-full bg-background shadow-lg ring-0 transition-transform",
          on ? "translate-x-4" : "translate-x-0"
        )}
      />
    </button>
  )
}

export { Switch }
