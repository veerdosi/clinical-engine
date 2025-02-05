export const ScenarioSchema = {
  title: String,
  difficulty: {
    type: String,
    enum: ['Beginner', 'Intermediate', 'Advanced']
  },
  category: String,
  duration: Number,
  description: String,
  createdAt: Date,
  completionRate: Number,
  attempts: Number,
  objectives: [String],
  requiredSkills: [String],
  medicalConditions: [String],
  patientProfile: {
    age: Number,
    gender: String,
    medicalHistory: [String],
    currentMedications: [String],
    vitalSigns: {
      bloodPressure: String,
      heartRate: Number,
      temperature: Number,
      respiratoryRate: Number,
      oxygenSaturation: Number
    }
  },
  correctPath: [{
    step: Number,
    action: String,
    reasoning: String
  }]
};