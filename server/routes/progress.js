import { Router } from 'express';
import { mongoClient, redis } from '../index.js';
import { ObjectId } from 'mongodb';

const router = Router();
const db = mongoClient.db('clinical-simulator');
const progress = db.collection('progress');

// Get user progress
router.get('/:userId', async (req, res) => {
  try {
    const userProgress = await progress.find({ 
      userId: req.params.userId 
    }).toArray();
    
    res.json(userProgress);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Record scenario attempt
router.post('/attempt', async (req, res) => {
  try {
    const { userId, scenarioId, score, decisions } = req.body;
    
    const result = await progress.insertOne({
      userId,
      scenarioId,
      score,
      decisions,
      completedAt: new Date()
    });

    // Update scenario stats in Redis
    const key = `scenario:${scenarioId}:stats`;
    await redis.hincrby(key, 'attempts', 1);
    await redis.hset(key, 'lastAttempt', new Date().toISOString());
    
    // Update average score
    const currentStats = await redis.hgetall(key);
    const newAvg = (parseFloat(currentStats.avgScore || 0) * parseInt(currentStats.attempts || 1) + score) / 
                   (parseInt(currentStats.attempts || 1) + 1);
    await redis.hset(key, 'avgScore', newAvg.toFixed(2));

    res.status(201).json({ id: result.insertedId });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export { router };