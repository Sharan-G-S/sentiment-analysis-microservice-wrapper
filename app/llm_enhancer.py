"""
LLM Enhancement Module - Groq and Gemini Integration
Provides advanced sentiment analysis with explanations and multi-language support
"""
import os
import json
import asyncio
from typing import Dict, Optional, List
from enum import Enum

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from app.logger import get_logger
from app.mock_llm import mock_enhancer

logger = get_logger(__name__)


class LLMProvider(str, Enum):
    """Available LLM providers"""
    GROQ = "groq"
    GEMINI = "gemini"
    AUTO = "auto"


class LLMEnhancer:
    """
    Enhances sentiment analysis with LLM-powered insights
    Provides explanations, context analysis, and advanced features
    """
    
    def __init__(self):
        self.groq_client = None
        self.gemini_model = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize available LLM clients"""
        # Initialize Groq
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and GROQ_AVAILABLE:
            try:
                self.groq_client = Groq(api_key=groq_key)
                logger.info("Groq client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq: {e}")
        
        # Initialize Gemini
        gemini_key = os.getenv("GOOGLE_API_KEY")
        if gemini_key and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
                logger.info("Gemini client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}")
    
    def is_available(self, provider: LLMProvider = LLMProvider.AUTO) -> bool:
        """Check if LLM enhancement is available"""
        if provider == LLMProvider.GROQ:
            return self.groq_client is not None
        elif provider == LLMProvider.GEMINI:
            return self.gemini_model is not None
        else:  # AUTO
            return self.groq_client is not None or self.gemini_model is not None
    
    async def explain_sentiment(
        self,
        text: str,
        sentiment: str,
        confidence: float,
        provider: LLMProvider = LLMProvider.AUTO
    ) -> Dict:
        """
        Generate detailed explanation for sentiment prediction
        
        Args:
            text: Input text
            sentiment: Predicted sentiment (positive/negative)
            confidence: Confidence score
            provider: LLM provider to use
        
        Returns:
            Dict with explanation, key_phrases, reasoning, suggestions
        """
        if not self.is_available(provider):
            logger.info("LLM not available, using mock enhancer")
            return mock_enhancer.explain_sentiment(text, sentiment, confidence)
        
        prompt = self._build_explanation_prompt(text, sentiment, confidence)
        
        try:
            if provider == LLMProvider.GROQ or (provider == LLMProvider.AUTO and self.groq_client):
                response = await self._query_groq(prompt)
            elif provider == LLMProvider.GEMINI or (provider == LLMProvider.AUTO and self.gemini_model):
                response = await self._query_gemini(prompt)
            else:
                return {"error": "No LLM provider available"}
            
            return self._parse_explanation_response(response)
        
        except Exception as e:
            logger.warning(f"LLM enhancement failed, falling back to mock: {e}")
            return mock_enhancer.explain_sentiment(text, sentiment, confidence)
    
    async def analyze_batch_insights(
        self,
        texts: List[str],
        sentiments: List[str],
        provider: LLMProvider = LLMProvider.AUTO
    ) -> Dict:
        """
        Analyze batch of texts and provide overall insights
        
        Args:
            texts: List of input texts
            sentiments: List of predicted sentiments
            provider: LLM provider to use
        
        Returns:
            Dict with trends, patterns, summary
        """
        if not self.is_available(provider):
            logger.info("LLM not available, using mock enhancer for batch insights")
            return mock_enhancer.analyze_batch_insights(texts, sentiments)
        
        prompt = self._build_batch_insights_prompt(texts, sentiments)
        
        try:
            if provider == LLMProvider.GROQ or (provider == LLMProvider.AUTO and self.groq_client):
                response = await self._query_groq(prompt)
            else:
                response = await self._query_gemini(prompt)
            
            return self._parse_insights_response(response)
        
        except Exception as e:
            logger.warning(f"Batch insights failed, falling back to mock: {e}")
            return mock_enhancer.analyze_batch_insights(texts, sentiments)
    
    async def detect_language_and_translate(
        self,
        text: str,
        provider: LLMProvider = LLMProvider.AUTO
    ) -> Dict:
        """
        Detect language and provide translation if needed
        
        Args:
            text: Input text
            provider: LLM provider to use
        
        Returns:
            Dict with language, translated_text, is_english
        """
        if not self.is_available(provider):
            return mock_enhancer.detect_language(text)
        
        prompt = f"""Analyze this text and provide:
1. Detected language (language code)
2. Whether it's English (true/false)
3. English translation if not English (or original text if English)

Text: "{text}"

Respond in JSON format:
{{
    "language": "language_code",
    "is_english": true/false,
    "translated_text": "translation or original"
}}"""
        
        try:
            if provider == LLMProvider.GROQ or (provider == LLMProvider.AUTO and self.groq_client):
                response = await self._query_groq(prompt)
            else:
                response = await self._query_gemini(prompt)
            
            return json.loads(response)
        
        except Exception as e:
            logger.warning(f"Language detection failed, using mock: {e}")
            return mock_enhancer.detect_language(text)
    
    def _build_explanation_prompt(self, text: str, sentiment: str, confidence: float) -> str:
        """Build prompt for sentiment explanation"""
        return f"""Analyze this sentiment prediction by examining ONLY the actual words present in the text:

Text: "{text}"
Predicted Sentiment: {sentiment}
Confidence: {confidence:.2%}

CRITICAL RULES:
1. Quote ONLY words that actually appear in the text - do not invent or assume content
2. For EACH key phrase, determine if it's positive or negative and estimate its sentiment weight (0-100%)
3. Analyze the ACTUAL sentiment of the words, not just what the model predicted
4. The model prediction shows what the ML model thinks, but you should analyze what the words actually mean
5. Explain why certain phrases have the sentiment they do based on their actual meaning

Provide a JSON response with:
1. explanation: Detailed explanation of the ACTUAL sentiment in the text based on the words present
2. key_phrases_detailed: Array of objects with phrase, sentiment (positive/negative), and score (0-100) based on actual word meaning
   Example: [{{"phrase": "disappointed", "sentiment": "negative", "score": 95}}, {{"phrase": "amazed", "sentiment": "positive", "score": 75}}]
3. overall_score: Overall sentiment breakdown based on analyzing all phrases {{"positive": X, "negative": Y}}
4. tone: Emotional intensity based on actual words used
5. context: What specific aspects are mentioned (quote actual topics from text)
6. evidence: Quote SPECIFIC words and explain their actual sentiment meaning
7. dominant_factor: Which phrase/word has the most sentiment weight and why
8. reasoning: Explain the actual sentiment composition of the text
9. suggestions: If negative sentiment detected, how to address the concerns mentioned

Format:
{{
    "explanation": "Explanation of actual sentiment based on word meanings",
    "key_phrases_detailed": [
        {{"phrase": "actual word/phrase", "sentiment": "positive|negative", "score": 0-100}}
    ],
    "overall_score": {{"positive": X, "negative": Y}},
    "tone": "emotional description based on actual words",
    "context": "actual aspects mentioned in text",
    "evidence": "Quoted words with their actual sentiment meanings",
    "dominant_factor": "Which word/phrase carries most sentiment weight",
    "reasoning": "Explanation of actual sentiment composition",
    "suggestions": ["specific suggestion 1", "specific suggestion 2"]
}}"""
    
    def _build_batch_insights_prompt(self, texts: List[str], sentiments: List[str]) -> str:
        """Build prompt for batch insights"""
        items = "\n".join([f"{i+1}. [{s}] {t}" for i, (t, s) in enumerate(zip(texts, sentiments))])
        
        return f"""Analyze these sentiment predictions and provide overall insights:

{items}

Provide a JSON response with:
1. summary: Overall summary of the sentiment trends
2. trends: Percentage breakdown of positive/negative
3. patterns: List of common themes or patterns observed

Format:
{{
    "summary": "Overall summary",
    "trends": {{"positive": X, "negative": Y}},
    "patterns": ["pattern1", "pattern2", ...]
}}"""
    
    async def _query_groq(self, prompt: str) -> str:
        """Query Groq API"""
        loop = asyncio.get_event_loop()
        
        def _make_request():
            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a sentiment analysis expert. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content
        
        return await loop.run_in_executor(None, _make_request)
    
    async def _query_gemini(self, prompt: str) -> str:
        """Query Gemini API"""
        loop = asyncio.get_event_loop()
        
        def _make_request():
            response = self.gemini_model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 1000,
                }
            )
            return response.text
        
        return await loop.run_in_executor(None, _make_request)
    
    def _parse_explanation_response(self, response: str) -> Dict:
        """Parse explanation response from LLM"""
        try:
            # Try to extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                parsed = json.loads(json_str)
                
                # Ensure all expected fields exist with defaults
                return {
                    "explanation": parsed.get("explanation", "No explanation provided"),
                    "key_phrases_detailed": parsed.get("key_phrases_detailed", []),
                    "overall_score": parsed.get("overall_score", {"positive": 0, "negative": 0, "neutral": 0}),
                    "tone": parsed.get("tone", "neutral"),
                    "context": parsed.get("context", "general"),
                    "evidence": parsed.get("evidence", "No specific evidence provided"),
                    "dominant_factor": parsed.get("dominant_factor", "Not specified"),
                    "reasoning": parsed.get("reasoning", "No detailed reasoning provided"),
                    "suggestions": parsed.get("suggestions", [])
                }
            else:
                return json.loads(response)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "explanation": response,
                "key_phrases_detailed": [],
                "overall_score": {"positive": 0, "negative": 0},
                "tone": "neutral",
                "context": "general",
                "evidence": "Raw response returned",
                "dominant_factor": "Unable to parse",
                "reasoning": "Unable to parse structured response",
                "suggestions": []
            }
    
    def _parse_insights_response(self, response: str) -> Dict:
        """Parse insights response from LLM"""
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return json.loads(response)
        except json.JSONDecodeError:
            return {
                "summary": response,
                "trends": {},
                "patterns": []
            }


# Global instance
llm_enhancer = LLMEnhancer()
