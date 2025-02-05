export const ProgressSchema = {
  userId: String,
  scenarioId: String,
  score: Number,
  decisions: [{
    timestamp: Date,
    action: String,
    result: String
  }],
  feedback: {
    strengths: [String],
    improvements: [String],
    overallScore: Number,
    categoryScores: {
      clinicalReasoning: Number,
      patientCommunication: Number,
      diagnosticAccuracy: Number,
      treatmentPlanning: Number
    }
  },
  completedAt: Date
};