import { Router } from 'express';
import { openai, redis } from '../index.js';

const router = Router();

// Generate patient dialogue
router.post('/dialogue', async (req, res) => {
  try {
    const { prompt, context, history } = req.body;
    
    // Check cache first
    const cacheKey = `dialogue:${Buffer.from(prompt).toString('base64')}`;
    const cachedResponse = await redis.get(cacheKey);
    
    if (cachedResponse) {
      return res.json(JSON.parse(cachedResponse));
    }

    const completion = await openai.chat.completions.create({
      model: "gpt-4",
      messages: [
        { 
          role: "system", 
          content: "You are a virtual patient in a medical training simulation. Respond naturally to the medical student's questions and exhibit the symptoms and behavior consistent with your condition."
        },
        ...history,
        { role: "user", content: prompt }
      ],
      temperature: 0.7,
      max_tokens: 150
    });

    const response = completion.choices[0].message;
    
    // Cache the response for 1 hour
    await redis.setex(cacheKey, 3600, JSON.stringify(response));
    
    res.json(response);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Generate diagnostic feedback
router.post('/feedback', async (req, res) => {
  try {
    const { decisions, correctPath } = req.body;
    
    const completion = await openai.chat.completions.create({
      model: "gpt-4",
      messages: [
        {
          role: "system",
          content: "You are a medical education AI providing feedback on clinical decisions."
        },
        {
          role: "user",
          content: `Compare these clinical decisions:\nStudent decisions: ${JSON.stringify(decisions)}\nBest practice path: ${JSON.stringify(correctPath)}`
        }
      ],
      temperature: 0.3,
      max_tokens: 300
    });

    res.json(completion.choices[0].message);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export { router };