import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

/**
 * GlassCard - Modern glassmorphism card component
 * Professional UI following 2025 design trends (Binance, Coinbase style)
 *
 * Features:
 * - Backdrop blur with depth
 * - Multi-layer professional shadows
 * - Gradient borders
 * - Smooth animations with framer-motion
 * - Hover states
 * - Dark mode optimized
 */

const GlassCard = React.forwardRef(({
  className,
  variant = "default",
  blur = "md",
  shadow = "lg",
  animate = true,
  hoverable = false,
  children,
  ...props
}, ref) => {
  const blurClasses = {
    sm: "backdrop-blur-sm",
    md: "backdrop-blur-md",
    lg: "backdrop-blur-lg",
    xl: "backdrop-blur-xl"
  }

  const shadowClasses = {
    sm: "shadow-[0_4px_16px_-4px_rgba(0,0,0,0.1)]",
    md: "shadow-[0_8px_24px_-6px_rgba(0,0,0,0.15)]",
    lg: "shadow-[0_12px_32px_-8px_rgba(0,0,0,0.2),0_0_0_1px_rgba(255,255,255,0.05)]",
    xl: "shadow-[0_20px_48px_-12px_rgba(0,0,0,0.25),0_0_0_1px_rgba(255,255,255,0.08)]"
  }

  const variantClasses = {
    default: "bg-background/40 border-white/10",
    glass: "bg-background/20 border-white/5",
    frosted: "bg-background/60 border-white/15",
    solid: "bg-background/95 border-white/20"
  }

  const baseClasses = cn(
    // Base structure
    "rounded-2xl border overflow-hidden",
    "transition-all duration-300 ease-out",

    // Glassmorphism effects
    blurClasses[blur],
    shadowClasses[shadow],
    variantClasses[variant],

    // Hover effects (if hoverable)
    hoverable && [
      "hover:bg-background/50",
      "hover:border-white/20",
      "hover:shadow-[0_16px_40px_-10px_rgba(0,0,0,0.3),0_0_0_1px_rgba(255,255,255,0.1)]",
      "hover:-translate-y-0.5",
      "cursor-pointer"
    ],

    // Custom classes
    className
  )

  const MotionDiv = animate ? motion.div : "div"
  const animationProps = animate ? {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }
  } : {}

  return (
    <MotionDiv
      ref={ref}
      className={baseClasses}
      {...animationProps}
      {...props}
    >
      {children}
    </MotionDiv>
  )
})
GlassCard.displayName = "GlassCard"

const GlassCardHeader = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "flex flex-col space-y-1.5 p-6",
      "border-b border-white/5",
      className
    )}
    {...props}
  />
))
GlassCardHeader.displayName = "GlassCardHeader"

const GlassCardTitle = React.forwardRef(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "text-xl font-semibold leading-none tracking-tight",
      "bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text",
      className
    )}
    {...props}
  />
))
GlassCardTitle.displayName = "GlassCardTitle"

const GlassCardDescription = React.forwardRef(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn(
      "text-sm text-muted-foreground/80",
      className
    )}
    {...props}
  />
))
GlassCardDescription.displayName = "GlassCardDescription"

const GlassCardContent = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("p-6 pt-4", className)}
    {...props}
  />
))
GlassCardContent.displayName = "GlassCardContent"

const GlassCardFooter = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "flex items-center p-6 pt-0",
      "border-t border-white/5 mt-auto",
      className
    )}
    {...props}
  />
))
GlassCardFooter.displayName = "GlassCardFooter"

// Stat Card - Specialized variant for metrics
const GlassStatCard = React.forwardRef(({
  title,
  value,
  change,
  trend,
  icon,
  className,
  ...props
}, ref) => {
  const trendColor = trend === 'up' ? 'text-green-500' : trend === 'down' ? 'text-red-500' : 'text-muted-foreground'
  const trendBg = trend === 'up' ? 'bg-green-500/10' : trend === 'down' ? 'bg-red-500/10' : 'bg-muted/20'

  return (
    <GlassCard
      ref={ref}
      variant="frosted"
      blur="lg"
      hoverable
      className={cn("relative group", className)}
      {...props}
    >
      <GlassCardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="space-y-2 flex-1">
            <p className="text-sm font-medium text-muted-foreground/80">
              {title}
            </p>
            <p className="text-3xl font-bold tracking-tight">
              {value}
            </p>
            {change && (
              <div className={cn("inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium", trendBg, trendColor)}>
                {trend === 'up' && '↑'}
                {trend === 'down' && '↓'}
                {change}
              </div>
            )}
          </div>
          {icon && (
            <div className="p-3 rounded-xl bg-primary/10 text-primary group-hover:scale-110 transition-transform duration-300">
              {icon}
            </div>
          )}
        </div>
      </GlassCardContent>
    </GlassCard>
  )
})
GlassStatCard.displayName = "GlassStatCard"

export {
  GlassCard,
  GlassCardHeader,
  GlassCardFooter,
  GlassCardTitle,
  GlassCardDescription,
  GlassCardContent,
  GlassStatCard
}
