import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center justify-center rounded-full border px-2.5 py-0.5 text-xs font-medium w-fit whitespace-nowrap shrink-0 [&>svg]:size-3 gap-1.5 transition-colors",
  {
    variants: {
      variant: {
        // Original variants
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        destructive: "border-transparent bg-destructive text-destructive-foreground",
        outline: "text-foreground",

        // Tailwind color variants with dark/light mode support
        slate: "border-transparent dark:bg-slate-500 bg-slate-600 text-white",
        "slate-subtle": "border-transparent dark:bg-slate-950 dark:text-slate-400 text-slate-600 bg-slate-100",

        gray: "border-transparent dark:bg-gray-500 bg-gray-600 text-white",
        "gray-subtle": "border-transparent dark:bg-gray-950 dark:text-gray-400 text-gray-600 bg-gray-100",

        zinc: "border-transparent dark:bg-zinc-500 bg-zinc-600 text-white",
        "zinc-subtle": "border-transparent dark:bg-zinc-950 dark:text-zinc-400 text-zinc-600 bg-zinc-100",

        neutral: "border-transparent dark:bg-neutral-500 bg-neutral-600 text-white",
        "neutral-subtle": "border-transparent dark:bg-neutral-950 dark:text-neutral-400 text-neutral-600 bg-neutral-100",

        stone: "border-transparent dark:bg-stone-500 bg-stone-600 text-white",
        "stone-subtle": "border-transparent dark:bg-stone-950 dark:text-stone-400 text-stone-600 bg-stone-100",

        red: "border-transparent dark:bg-red-500 bg-red-600 text-white",
        "red-subtle": "border-transparent dark:bg-red-950 dark:text-red-400 text-red-600 bg-red-100",

        orange: "border-transparent dark:bg-orange-500 bg-orange-600 text-white",
        "orange-subtle": "border-transparent dark:bg-orange-950 dark:text-orange-400 text-orange-600 bg-orange-100",

        amber: "border-transparent dark:bg-amber-500 bg-amber-600 text-white",
        "amber-subtle": "border-transparent dark:bg-amber-950 dark:text-amber-400 text-amber-600 bg-amber-100",

        yellow: "border-transparent dark:bg-yellow-500 bg-yellow-600 text-white",
        "yellow-subtle": "border-transparent dark:bg-yellow-950 dark:text-yellow-400 text-yellow-600 bg-yellow-100",

        lime: "border-transparent dark:bg-lime-500 bg-lime-600 text-white",
        "lime-subtle": "border-transparent dark:bg-lime-950 dark:text-lime-400 text-lime-600 bg-lime-100",

        green: "border-transparent dark:bg-green-500 bg-green-600 text-white",
        "green-subtle": "border-transparent dark:bg-green-950 dark:text-green-400 text-green-600 bg-green-100",

        emerald: "border-transparent dark:bg-emerald-500 bg-emerald-600 text-white",
        "emerald-subtle": "border-transparent dark:bg-emerald-950 dark:text-emerald-400 text-emerald-600 bg-emerald-100",

        teal: "border-transparent dark:bg-teal-500 bg-teal-600 text-white",
        "teal-subtle": "border-transparent dark:bg-teal-950 dark:text-teal-400 text-teal-600 bg-teal-100",

        cyan: "border-transparent dark:bg-cyan-500 bg-cyan-600 text-white",
        "cyan-subtle": "border-transparent dark:bg-cyan-950 dark:text-cyan-400 text-cyan-600 bg-cyan-100",

        sky: "border-transparent dark:bg-sky-500 bg-sky-600 text-white",
        "sky-subtle": "border-transparent dark:bg-sky-950 dark:text-sky-400 text-sky-600 bg-sky-100",

        blue: "border-transparent dark:bg-blue-500 bg-blue-600 text-white",
        "blue-subtle": "border-transparent dark:bg-blue-950 dark:text-blue-400 text-blue-600 bg-blue-100",

        indigo: "border-transparent dark:bg-indigo-500 bg-indigo-600 text-white",
        "indigo-subtle": "border-transparent dark:bg-indigo-950 dark:text-indigo-400 text-indigo-600 bg-indigo-100",

        violet: "border-transparent dark:bg-violet-500 bg-violet-600 text-white",
        "violet-subtle": "border-transparent dark:bg-violet-950 dark:text-violet-400 text-violet-600 bg-violet-100",

        purple: "border-transparent dark:bg-purple-500 bg-purple-600 text-white",
        "purple-subtle": "border-transparent dark:bg-purple-950 dark:text-purple-400 text-purple-600 bg-purple-100",

        fuchsia: "border-transparent dark:bg-fuchsia-500 bg-fuchsia-600 text-white",
        "fuchsia-subtle": "border-transparent dark:bg-fuchsia-950 dark:text-fuchsia-400 text-fuchsia-600 bg-fuchsia-100",

        pink: "border-transparent dark:bg-pink-500 bg-pink-600 text-white",
        "pink-subtle": "border-transparent dark:bg-pink-950 dark:text-pink-400 text-pink-600 bg-pink-100",

        rose: "border-transparent dark:bg-rose-500 bg-rose-600 text-white",
        "rose-subtle": "border-transparent dark:bg-rose-950 dark:text-rose-400 text-rose-600 bg-rose-100",
      },
      size: {
        sm: "text-[10px] px-2 py-0 h-[18px]",
        md: "text-xs px-2.5 py-0.5 h-[22px]",
        lg: "text-sm px-3 py-1 h-[26px]",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
  VariantProps<typeof badgeVariants> {
  icon?: React.ReactNode
}

function Badge({
  className,
  variant,
  size,
  icon,
  children,
  ...props
}: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant, size }), className)} {...props}>
      {icon && <span className="shrink-0">{icon}</span>}
      {children}
    </div>
  )
}

export { Badge, badgeVariants }