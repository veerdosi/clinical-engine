import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { MongoClient } from 'mongodb';
import Redis from 'ioredis';
import { OpenAI } from 'openai';
import { router as scenariosRouter } from './routes/scenarios.js';
import { router as progressRouter } from './routes/progress.js';
import { router as aiRouter } from './routes/ai.js';

dotenv.config();

const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Database connections
export const mongoClient = new MongoClient(process.env.MONGODB_URI);
export const redis = new Redis(process.env.REDIS_URL);
export const openai = new OpenAI(process.env.OPENAI_API_KEY);

// Routes
app.use('/api/scenarios', scenariosRouter);
app.use('/api/progress', progressRouter);
app.use('/api/ai', aiRouter);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

// Connect to databases and start server
async function startServer() {
  try {
    await mongoClient.connect();
    console.log('Connected to MongoDB');

    await redis.ping();
    console.log('Connected to Redis');

    app.listen(port, () => {
      console.log(`Server running on port ${port}`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();