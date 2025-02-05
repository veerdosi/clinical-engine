import { Router } from 'express';
import { mongoClient } from '../index.js';
import { ObjectId } from 'mongodb';

const router = Router();
const db = mongoClient.db('clinical-simulator');
const scenarios = db.collection('scenarios');

// Get all scenarios with optional filtering
router.get('/', async (req, res) => {
  try {
    const { difficulty, category } = req.query;
    const filter = {};
    
    if (difficulty) filter.difficulty = difficulty;
    if (category) filter.category = category;
    
    const result = await scenarios.find(filter).toArray();
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get a specific scenario by ID
router.get('/:id', async (req, res) => {
  try {
    const scenario = await scenarios.findOne({ _id: new ObjectId(req.params.id) });
    if (!scenario) {
      return res.status(404).json({ error: 'Scenario not found' });
    }
    res.json(scenario);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Create a new scenario
router.post('/', async (req, res) => {
  try {
    const { title, difficulty, category, duration, description } = req.body;
    const result = await scenarios.insertOne({
      title,
      difficulty,
      category,
      duration,
      description,
      createdAt: new Date(),
      completionRate: 0,
      attempts: 0
    });
    res.status(201).json({ id: result.insertedId });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export { router };