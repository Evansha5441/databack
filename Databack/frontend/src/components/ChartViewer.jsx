import React from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Bar, Line, Pie, Scatter } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
)

export default function ChartViewer({ spec, data }) {
  if (!spec || !spec.recommended || !data || !Array.isArray(data) || data.length === 0) {
    return null
  }

  const { type = 'bar', x_key, y_key, title = 'Data Visualization' } = spec

  const labels = data.slice(0, 15).map(row => String(row[x_key] || ''))
  const values = data.slice(0, 15).map(row => Number(row[y_key]) || 0)

  const palette = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
    '#ec4899', '#06b6d4', '#14b8a6', '#f97316', '#6366f1'
  ]

  const chartData = {
    labels: labels,
    datasets: [
      {
        label: y_key ? y_key.replace('_', ' ').toUpperCase() : 'Value',
        data: values,
        backgroundColor: type === 'pie' ? palette : 'rgba(59, 130, 246, 0.75)',
        borderColor: type === 'line' ? '#3b82f6' : 'rgba(59, 130, 246, 1)',
        borderWidth: 2,
        tension: 0.3
      }
    ]
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: { color: '#94a3b8' }
      },
      title: {
        display: true,
        text: title,
        color: '#f8fafc',
        font: { size: 14 }
      }
    },
    scales: type === 'pie' ? {} : {
      x: {
        ticks: { color: '#94a3b8' },
        grid: { color: '#1e293b' }
      },
      y: {
        ticks: { color: '#94a3b8' },
        grid: { color: '#1e293b' }
      }
    }
  }

  return (
    <div className="chart-container">
      {type === 'bar' && <Bar data={chartData} options={options} />}
      {type === 'line' && <Line data={chartData} options={options} />}
      {type === 'pie' && <Pie data={chartData} options={options} />}
      {type === 'scatter' && (
        <Scatter
          data={{
            datasets: [{
              label: `${x_key} vs ${y_key}`,
              data: data.slice(0, 30).map(row => ({
                x: Number(row[x_key]) || 0,
                y: Number(row[y_key]) || 0
              })),
              backgroundColor: '#ef4444'
            }]
          }}
          options={options}
        />
      )}
    </div>
  )
}
