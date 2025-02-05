import React from 'react';
import { Brain } from 'lucide-react';
import { ScenarioCard } from './components/ScenarioCard';
import { PerformanceChart } from './components/PerformanceChart';
import { RecentActivityList } from './components/RecentActivity';
import type { Scenario, PerformanceMetric, RecentActivity } from './types';

// Sample data
const scenarios: Scenario[] = [
  {
    id: '1',
    title: 'Emergency Room Triage',
    difficulty: 'Intermediate',
    category: 'Emergency Medicine',
    duration: 30,
    completionRate: 75,
    description: 'Practice prioritizing patient care in a busy ER setting.'
  },
  {
    id: '2',
    title: 'Cardiac Assessment',
    difficulty: 'Advanced',
    category: 'Cardiology',
    duration: 45,
    completionRate: 60,
    description: 'Perform a comprehensive cardiac evaluation and diagnosis.'
  },
  {
    id: '3',
    title: 'Basic Patient Interview',
    difficulty: 'Beginner',
    category: 'General Practice',
    duration: 20,
    completionRate: 90,
    description: 'Learn the fundamentals of patient communication and history taking.'
  }
];

const performanceMetrics: PerformanceMetric[] = [
  { category: 'Clinical Reasoning', score: 85, total: 100, improvement: 5 },
  { category: 'Patient Communication', score: 92, total: 100, improvement: 8 },
  { category: 'Diagnostic Accuracy', score: 78, total: 100, improvement: -2 },
  { category: 'Treatment Planning', score: 88, total: 100, improvement: 4 }
];

const recentActivities: RecentActivity[] = [
  {
    id: '1',
    scenarioName: 'Emergency Room Triage',
    date: '2 hours ago',
    score: 85,
    status: 'completed'
  },
  {
    id: '2',
    scenarioName: 'Cardiac Assessment',
    date: 'Yesterday',
    score: 72,
    status: 'in-progress'
  },
  {
    id: '3',
    scenarioName: 'Basic Patient Interview',
    date: '2 days ago',
    score: 65,
    status: 'failed'
  }
];

function App() {
  const handleScenarioClick = (id: string) => {
    console.log('Scenario clicked:', id);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Brain className="w-8 h-8 text-blue-600" />
              <h1 className="ml-2 text-xl font-semibold text-gray-900">
                Clinical Training Simulator
              </h1>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Available Scenarios */}
          <div className="lg:col-span-2 space-y-6">
            <h2 className="text-xl font-semibold text-gray-900">Available Scenarios</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {scenarios.map((scenario) => (
                <ScenarioCard
                  key={scenario.id}
                  scenario={scenario}
                  onClick={handleScenarioClick}
                />
              ))}
            </div>
          </div>

          {/* Right Column - Performance & Activity */}
          <div className="space-y-6">
            <PerformanceChart metrics={performanceMetrics} />
            <RecentActivityList activities={recentActivities} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;