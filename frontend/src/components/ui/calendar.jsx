import * as React from "react"

import { cn } from "@/lib/utils"

/**
 * Lightweight calendar input replacement without external dependencies.
 * Provides a styled date input that mimics the API used previously.
 */
const Calendar = React.forwardRef(({ className, ...props }, ref) => {
  return (
    <input
      ref={ref}
      type="date"
      className={cn(
        "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background",
        "placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        className
      )}
      {...props}
    />
  )
})

Calendar.displayName = "Calendar"

export { Calendar }
