import React from 'react';
import { Clock, BarChart2, Trophy } from 'lucide-react';
import type { Scenario } from '../types';

interface ScenarioCardProps {
  scenario: Scenario;
  onClick: (id: string) => void;
}

export function ScenarioCard({ scenario, onClick }: ScenarioCardProps) {
  const difficultyColor = {
    Beginner: 'bg-green-100 text-green-800',
    Intermediate: 'bg-yellow-100 text-yellow-800',
    Advanced: 'bg-red-100 text-red-800',
  }[scenario.difficulty];

  return (
    <div 
      onClick={() => onClick(scenario.id)}
      className="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow p-6 cursor-pointer border border-gray-100"
    >
      <div className="flex justify-between items-start mb-4">
        <h3 className="font-semibold text-lg text-gray-900">{scenario.title}</h3>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${difficultyColor}`}>
          {scenario.difficulty}
        </span>
      </div>
      
      <p className="text-gray-600 text-sm mb-4">{scenario.description}</p>
      
      <div className="flex items-center justify-between text-sm text-gray-500">
        <div className="flex items-center gap-1">
          <Clock className="w-4 h-4" />
          <span>{scenario.duration}m</span>
        </div>
        
        {scenario.completionRate && (
          <div className="flex items-center gap-1">
            <Trophy className="w-4 h-4" />
            <span>{scenario.completionRate}% completion rate</span>
          </div>
        )}
      </div>
    </div>
  );
}