import * as React from "react"

import { cn } from "@/lib/utils"

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "border-[#E8E0D4] placeholder:text-[#9a918a] focus-visible:border-orange-300 focus-visible:ring-orange-200/50 aria-invalid:ring-red-200 aria-invalid:border-red-400 flex field-sizing-content min-h-16 w-full rounded-xl border bg-[#F5F0E8] px-3 py-2 text-base text-[#2D2A26] shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        className
      )}
      {...props}
    />
  )
}

export { Textarea }
