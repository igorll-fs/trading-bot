import * as React from "react"
import Skeleton from 'react-loading-skeleton'
import 'react-loading-skeleton/dist/skeleton.css'
import { GlassCard, GlassCardContent, GlassCardHeader } from "./glass-card"
import { cn } from "@/lib/utils"

/**
 * SkeletonCard - Professional loading states with glassmorphism
 * Uses react-loading-skeleton for smooth, shimmer effects
 *
 * Variants:
 * - stat: For metric cards (balance, PnL, etc)
 * - chart: For chart containers
 * - table: For data tables
 * - list: For list items
 */

const SkeletonCard = React.forwardRef(({
  variant = "default",
  className,
  rows = 3,
  ...props
}, ref) => {
  const renderContent = () => {
    switch (variant) {
      case "stat":
        return (
          <GlassCard ref={ref} variant="frosted" className={cn("p-6", className)} {...props}>
            <div className="space-y-3">
              <Skeleton width={120} height={16} className="opacity-60" />
              <Skeleton width={180} height={36} />
              <Skeleton width={80} height={24} className="opacity-40" />
            </div>
          </GlassCard>
        )

      case "chart":
        return (
          <GlassCard ref={ref} variant="frosted" className={cn("p-6", className)} {...props}>
            <div className="space-y-4">
              <Skeleton width={150} height={20} />
              <Skeleton height={200} className="rounded-lg" />
            </div>
          </GlassCard>
        )

      case "table":
        return (
          <GlassCard ref={ref} variant="frosted" className={className} {...props}>
            <GlassCardHeader>
              <Skeleton width={200} height={24} />
            </GlassCardHeader>
            <GlassCardContent className="space-y-2">
              {Array.from({ length: rows }).map((_, i) => (
                <div key={i} className="flex items-center justify-between py-2">
                  <Skeleton width={120} height={16} />
                  <Skeleton width={80} height={16} />
                </div>
              ))}
            </GlassCardContent>
          </GlassCard>
        )

      case "list":
        return (
          <GlassCard ref={ref} variant="frosted" className={className} {...props}>
            <GlassCardContent className="space-y-3 p-4">
              {Array.from({ length: rows }).map((_, i) => (
                <div key={i} className="flex items-center gap-3">
                  <Skeleton circle width={40} height={40} />
                  <div className="flex-1 space-y-2">
                    <Skeleton width="60%" height={16} />
                    <Skeleton width="40%" height={12} className="opacity-60" />
                  </div>
                </div>
              ))}
            </GlassCardContent>
          </GlassCard>
        )

      default:
        return (
          <GlassCard ref={ref} variant="frosted" className={className} {...props}>
            <GlassCardContent className="space-y-3 p-6">
              <Skeleton height={20} />
              <Skeleton height={16} className="opacity-80" />
              <Skeleton height={16} width="80%" className="opacity-60" />
            </GlassCardContent>
          </GlassCard>
        )
    }
  }

  return renderContent()
})
SkeletonCard.displayName = "SkeletonCard"

// Skeleton Grid - For dashboard layouts
const SkeletonGrid = ({ columns = 3, rows = 2, variant = "stat" }) => {
  return (
    <div className={cn(
      "grid gap-6",
      columns === 2 && "grid-cols-1 md:grid-cols-2",
      columns === 3 && "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
      columns === 4 && "grid-cols-1 md:grid-cols-2 lg:grid-cols-4"
    )}>
      {Array.from({ length: columns * rows }).map((_, i) => (
        <SkeletonCard key={i} variant={variant} />
      ))}
    </div>
  )
}
SkeletonGrid.displayName = "SkeletonGrid"

// Individual skeleton components for granular control
const SkeletonStat = () => (
  <SkeletonCard variant="stat" />
)

const SkeletonChart = () => (
  <SkeletonCard variant="chart" />
)

const SkeletonTable = ({ rows = 5 }) => (
  <SkeletonCard variant="table" rows={rows} />
)

const SkeletonList = ({ items = 3 }) => (
  <SkeletonCard variant="list" rows={items} />
)

export {
  SkeletonCard,
  SkeletonGrid,
  SkeletonStat,
  SkeletonChart,
  SkeletonTable,
  SkeletonList
}
