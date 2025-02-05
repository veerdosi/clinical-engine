export interface Scenario {
  id: string;
  title: string;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  category: string;
  duration: number; // in minutes
  completionRate?: number;
  description: string;
}

export interface PerformanceMetric {
  category: string;
  score: number;
  total: number;
  improvement: number; // percentage
}

export interface RecentActivity {
  id: string;
  scenarioName: string;
  date: string;
  score: number;
  status: 'completed' | 'in-progress' | 'failed';
}