/**
 * SparklineChart - Mini-chart de linha para cards
 * 
 * Criado por: SessionA (Backend)
 * Para: SessionB (Frontend) usar nos GlassStatCard
 * 
 * Features:
 * - SVG leve (sem libs pesadas)
 * - Gradiente verde/vermelho baseado em tendência
 * - Animação suave
 * - Responsive
 */

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

export function SparklineChart({ 
  data = [], 
  width = 120, 
  height = 40,
  className,
  showArea = true,
  strokeWidth = 2,
  animated = true
}) {
  const chartData = useMemo(() => {
    if (!data?.length) return null;
    
    // Extrair valores
    const values = data.map(d => d.value ?? d.pnl ?? 0);
    
    // Calcular min/max para normalização
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;
    
    // Determinar tendência (último vs primeiro)
    const trend = values[values.length - 1] > values[0] ? 'up' : 
                  values[values.length - 1] < values[0] ? 'down' : 'neutral';
    
    // Criar pontos SVG
    const points = values.map((value, index) => {
      const x = (index / (values.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return { x, y };
    });
    
    // Criar path
    const pathD = points
      .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`)
      .join(' ');
    
    // Criar área (path fechado)
    const areaD = pathD + ` L ${width} ${height} L 0 ${height} Z`;
    
    return { points, pathD, areaD, trend, min, max, last: values[values.length - 1] };
  }, [data, width, height]);

  if (!chartData) {
    return (
      <div 
        className={cn("flex items-center justify-center", className)}
        style={{ width, height }}
      >
        <span className="text-xs text-muted-foreground">No data</span>
      </div>
    );
  }

  const colors = {
    up: { stroke: '#10b981', fill: 'url(#sparkline-gradient-up)' },
    down: { stroke: '#ef4444', fill: 'url(#sparkline-gradient-down)' },
    neutral: { stroke: '#6b7280', fill: 'url(#sparkline-gradient-neutral)' }
  };

  const color = colors[chartData.trend];

  const ChartWrapper = animated ? motion.svg : 'svg';
  const animationProps = animated ? {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.5 }
  } : {};

  return (
    <ChartWrapper
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={cn("overflow-visible", className)}
      {...animationProps}
    >
      {/* Gradients */}
      <defs>
        <linearGradient id="sparkline-gradient-up" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#10b981" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="sparkline-gradient-down" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#ef4444" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="sparkline-gradient-neutral" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#6b7280" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#6b7280" stopOpacity="0" />
        </linearGradient>
      </defs>
      
      {/* Area fill */}
      {showArea && (
        <path
          d={chartData.areaD}
          fill={color.fill}
          className="transition-all duration-300"
        />
      )}
      
      {/* Line */}
      <path
        d={chartData.pathD}
        fill="none"
        stroke={color.stroke}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        className="transition-all duration-300"
      />
      
      {/* End point dot */}
      <circle
        cx={chartData.points[chartData.points.length - 1].x}
        cy={chartData.points[chartData.points.length - 1].y}
        r={3}
        fill={color.stroke}
        className="transition-all duration-300"
      />
    </ChartWrapper>
  );
}

/**
 * GlassStatCard com Sparkline integrado
 * Exemplo de uso para SessionB
 */
export function GlassStatCardWithSparkline({
  title,
  value,
  subtitle,
  sparklineData,
  trend,
  icon: Icon,
  className
}) {
  return (
    <div className={cn(
      "relative rounded-2xl border overflow-hidden p-6",
      "bg-background/40 backdrop-blur-md border-white/10",
      "shadow-[0_12px_32px_-8px_rgba(0,0,0,0.2),0_0_0_1px_rgba(255,255,255,0.05)]",
      "transition-all duration-300 hover:bg-background/50",
      className
    )}>
      <div className="flex justify-between items-start mb-2">
        <span className="text-sm text-muted-foreground">{title}</span>
        {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
      </div>
      
      <div className="flex items-end justify-between">
        <div>
          <div className="text-2xl font-bold">{value}</div>
          {subtitle && (
            <div className={cn(
              "text-sm",
              trend === 'up' && "text-emerald-500",
              trend === 'down' && "text-red-500",
              trend === 'neutral' && "text-muted-foreground"
            )}>
              {subtitle}
            </div>
          )}
        </div>
        
        {sparklineData && (
          <SparklineChart 
            data={sparklineData} 
            width={80} 
            height={32}
            className="ml-4"
          />
        )}
      </div>
    </div>
  );
}

export default SparklineChart;
