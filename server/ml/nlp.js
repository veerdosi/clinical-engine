import { openai } from '../index.js';
import natural from 'natural';
import { redis } from '../index.js';

const tokenizer = new natural.WordTokenizer();
const tfidf = new natural.TfIdf();

export class NLPProcessor {
  async analyzePatientInteraction(conversation) {
    try {
      // Analyze conversation sentiment and key medical terms
      const tokens = conversation.map(msg => tokenizer.tokenize(msg.content.toLowerCase()));
      
      // Extract medical terms and symptoms
      const medicalTerms = await this.extractMedicalTerms(tokens.flat());
      
      // Analyze communication style
      const communicationAnalysis = await this.analyzeCommunicationStyle(conversation);
      
      return {
        medicalTerms,
        communicationAnalysis,
        timestamp: new Date()
      };
    } catch (error) {
      console.error('NLP Analysis Error:', error);
      throw error;
    }
  }

  async extractMedicalTerms(tokens) {
    const cacheKey = `medical-terms:${tokens.join('-')}`;
    const cached = await redis.get(cacheKey);
    
    if (cached) return JSON.parse(cached);

    const completion = await openai.chat.completions.create({
      model: "gpt-4",
      messages: [{
        role: "system",
        content: "Extract and categorize medical terms from the following text into: symptoms, conditions, medications, and procedures."
      }, {
        role: "user",
        content: tokens.join(' ')
      }],
      temperature: 0.3
    });

    const result = completion.choices[0].message.content;
    await redis.setex(cacheKey, 3600, JSON.stringify(result));
    
    return result;
  }

  async analyzeCommunicationStyle(conversation) {
    const analysis = await openai.chat.completions.create({
      model: "gpt-4",
      messages: [{
        role: "system",
        content: "Analyze the medical professional's communication style for: empathy, clarity, professionalism, and patient engagement."
      }, {
        role: "user",
        content: JSON.stringify(conversation)
      }],
      temperature: 0.3
    });

    return analysis.choices[0].message.content;
  }
}