import React from 'react';
import { BarChart2 } from 'lucide-react';
import type { PerformanceMetric } from '../types';

interface PerformanceChartProps {
  metrics: PerformanceMetric[];
}

export function PerformanceChart({ metrics }: PerformanceChartProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Performance Overview</h2>
        <BarChart2 className="w-5 h-5 text-gray-400" />
      </div>
      
      <div className="space-y-4">
        {metrics.map((metric) => (
          <div key={metric.category}>
            <div className="flex justify-between mb-1">
              <span className="text-sm font-medium text-gray-700">{metric.category}</span>
              <span className="text-sm text-gray-500">{metric.score}/{metric.total}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: `${(metric.score / metric.total) * 100}%` }}
              />
            </div>
            <div className="mt-1">
              <span className={`text-xs ${metric.improvement >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {metric.improvement >= 0 ? '↑' : '↓'} {Math.abs(metric.improvement)}% from last week
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}