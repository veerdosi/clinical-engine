import React from 'react';
import { CheckCircle, Clock, XCircle } from 'lucide-react';
import type { RecentActivity } from '../types';

interface RecentActivityProps {
  activities: RecentActivity[];
}

export function RecentActivityList({ activities }: RecentActivityProps) {
  const getStatusIcon = (status: RecentActivity['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'in-progress':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">Recent Activity</h2>
      <div className="space-y-4">
        {activities.map((activity) => (
          <div key={activity.id} className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {getStatusIcon(activity.status)}
              <div>
                <h3 className="text-sm font-medium text-gray-900">{activity.scenarioName}</h3>
                <p className="text-sm text-gray-500">{activity.date}</p>
              </div>
            </div>
            <span className="text-sm font-medium text-gray-900">{activity.score}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}