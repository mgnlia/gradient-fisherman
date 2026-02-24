'use client'

import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  ScatterChart, Scatter, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

interface ChartConfig {
  chart_type: 'bar' | 'line' | 'pie' | 'scatter' | 'area'
  title: string
  data: Record<string, unknown>[]
  x_key: string
  y_keys: string[]
  colors?: string[]
}

const DEFAULT_COLORS = ['#0080FF', '#00B4D8', '#48CAE4', '#90E0EF', '#ADE8F4', '#0057B3']

function formatLabel(value: string | number): string {
  if (typeof value === 'string' && value.length > 12) {
    return value.substring(0, 12) + '…'
  }
  return String(value)
}

function formatValue(value: unknown): string {
  if (typeof value === 'number') {
    if (value > 1000) return value.toLocaleString('en-US', { maximumFractionDigits: 0 })
    return value.toFixed(2)
  }
  return String(value)
}

export default function ChartRenderer({ chart }: { chart: ChartConfig }) {
  const colors = chart.colors || DEFAULT_COLORS
  const data = chart.data.slice(0, 20)

  const commonProps = {
    data,
    margin: { top: 10, right: 20, left: 10, bottom: 60 },
  }

  const axisStyle = {
    fill: '#94a3b8',
    fontSize: 11,
  }

  const tooltipStyle = {
    backgroundColor: '#0d2040',
    border: '1px solid rgba(0,128,255,0.3)',
    borderRadius: '8px',
    color: '#e2e8f0',
    fontSize: 12,
  }

  const renderChart = () => {
    switch (chart.chart_type) {
      case 'bar':
        return (
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
            <XAxis dataKey={chart.x_key} tick={axisStyle} angle={-35} textAnchor="end" height={70} tickFormatter={formatLabel} />
            <YAxis tick={axisStyle} tickFormatter={formatValue} />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 12 }} />
            {chart.y_keys.map((key, i) => (
              <Bar key={key} dataKey={key} fill={colors[i % colors.length]} radius={[4, 4, 0, 0]} />
            ))}
          </BarChart>
        )

      case 'line':
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
            <XAxis dataKey={chart.x_key} tick={axisStyle} angle={-35} textAnchor="end" height={70} tickFormatter={formatLabel} />
            <YAxis tick={axisStyle} tickFormatter={formatValue} />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 12 }} />
            {chart.y_keys.map((key, i) => (
              <Line key={key} type="monotone" dataKey={key} stroke={colors[i % colors.length]} strokeWidth={2} dot={{ r: 3 }} />
            ))}
          </LineChart>
        )

      case 'area':
        return (
          <AreaChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
            <XAxis dataKey={chart.x_key} tick={axisStyle} angle={-35} textAnchor="end" height={70} tickFormatter={formatLabel} />
            <YAxis tick={axisStyle} tickFormatter={formatValue} />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 12 }} />
            {chart.y_keys.map((key, i) => (
              <Area key={key} type="monotone" dataKey={key} stroke={colors[i % colors.length]} fill={`${colors[i % colors.length]}33`} strokeWidth={2} />
            ))}
          </AreaChart>
        )

      case 'pie':
        return (
          <PieChart>
            <Pie
              data={data}
              dataKey={chart.y_keys[0] || 'value'}
              nameKey={chart.x_key}
              cx="50%"
              cy="50%"
              outerRadius={110}
              label={({ name, percent }) => `${formatLabel(name)} ${(percent * 100).toFixed(0)}%`}
              labelLine={{ stroke: 'rgba(255,255,255,0.3)' }}
            >
              {data.map((_, index) => (
                <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={tooltipStyle} />
            <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 12 }} />
          </PieChart>
        )

      case 'scatter':
        return (
          <ScatterChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
            <XAxis dataKey={chart.x_key} tick={axisStyle} name={chart.x_key} />
            <YAxis dataKey={chart.y_keys[0]} tick={axisStyle} name={chart.y_keys[0]} />
            <Tooltip contentStyle={tooltipStyle} cursor={{ strokeDasharray: '3 3' }} />
            <Scatter name={chart.y_keys[0]} data={data} fill={colors[0]} />
          </ScatterChart>
        )

      default:
        return null
    }
  }

  return (
    <div className="mt-3 rounded-xl overflow-hidden" style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(0,128,255,0.2)' }}>
      <div className="px-4 pt-3 pb-1">
        <h3 className="text-sm font-semibold text-ocean-300 flex items-center gap-2">
          <span>📊</span>
          <span>{chart.title}</span>
        </h3>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        {renderChart() || <div />}
      </ResponsiveContainer>
    </div>
  )
}
