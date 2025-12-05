"""
Test/Demo mode for LLM Enhancement
Provides simulated responses when API keys are not available or for testing
"""
from typing import Dict, List


class MockLLMEnhancer:
    """Mock LLM enhancer for testing and demonstration"""
    
    @staticmethod
    def explain_sentiment(text: str, sentiment: str, confidence: float) -> Dict:
        """Generate mock sentiment explanation"""
        if sentiment == "positive":
            return {
                "explanation": f"The text expresses strong positive sentiment with {confidence:.1%} confidence. Words like 'amazing', 'love', 'great', and 'excellent' indicate enthusiasm and satisfaction.",
                "key_phrases": [
                    phrase for phrase in ["amazing", "love it", "excellent", "great", "wonderful", "fantastic"]
                    if phrase.lower() in text.lower()
                ][:5] or ["positive language", "enthusiastic tone"],
                "reasoning": "The text uses superlative language and emotional expressions that clearly indicate a positive experience. The strong conviction in the wording (e.g., 'absolutely', 'so much') reinforces the positive sentiment.",
                "suggestions": []
            }
        else:  # negative
            suggestions = [
                "Consider addressing the specific pain points mentioned",
                "Implement quality control measures to prevent similar issues",
                "Improve customer support response time",
                "Offer solutions or compensation for negative experiences"
            ]
            return {
                "explanation": f"The text expresses strong negative sentiment with {confidence:.1%} confidence. Words like 'terrible', 'worst', 'awful', and 'disappointed' indicate dissatisfaction and frustration.",
                "key_phrases": [
                    phrase for phrase in ["terrible", "worst", "awful", "disappointed", "waste", "horrible", "poor"]
                    if phrase.lower() in text.lower()
                ][:5] or ["negative language", "critical tone"],
                "reasoning": "The text contains strong negative indicators and critical language. The intensity of the criticism (e.g., 'worst ever', 'complete waste') suggests a deeply negative experience.",
                "suggestions": suggestions[:3]
            }
    
    @staticmethod
    def analyze_batch_insights(texts: List[str], sentiments: List[str]) -> Dict:
        """Generate mock batch insights"""
        total = len(sentiments)
        positive_count = sentiments.count("positive")
        negative_count = sentiments.count("negative")
        
        positive_pct = (positive_count / total * 100) if total > 0 else 0
        negative_pct = (negative_count / total * 100) if total > 0 else 0
        
        # Determine overall trend
        if positive_pct > 70:
            summary = f"Overwhelmingly positive sentiment detected across {total} texts ({positive_pct:.1f}% positive). The majority of feedback indicates satisfaction."
        elif negative_pct > 70:
            summary = f"Predominantly negative sentiment detected across {total} texts ({negative_pct:.1f}% negative). Critical feedback requires attention."
        elif positive_pct > negative_pct:
            summary = f"Generally positive sentiment with mixed feedback across {total} texts ({positive_pct:.1f}% positive, {negative_pct:.1f}% negative)."
        elif negative_pct > positive_pct:
            summary = f"Leaning negative with mixed sentiment across {total} texts ({negative_pct:.1f}% negative, {positive_pct:.1f}% positive)."
        else:
            summary = f"Evenly split sentiment across {total} texts ({positive_pct:.1f}% positive, {negative_pct:.1f}% negative)."
        
        # Identify patterns
        patterns = []
        if positive_count > 0:
            patterns.append(f"Customer satisfaction themes in {positive_count} reviews")
        if negative_count > 0:
            patterns.append(f"Service/product concerns in {negative_count} reviews")
        if total >= 5:
            patterns.append("Diverse feedback across multiple touchpoints")
        
        return {
            "summary": summary,
            "trends": {
                "positive": round(positive_pct, 1),
                "negative": round(negative_pct, 1)
            },
            "patterns": patterns,
            "recommendation": "Focus on addressing negative feedback while maintaining positive experiences" if negative_count > 0 else "Continue current practices to maintain positive sentiment"
        }
    
    @staticmethod
    def detect_language(text: str) -> Dict:
        """Mock language detection"""
        # Simple heuristic - check for common non-English characters
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
        has_arabic = any('\u0600' <= char <= '\u06ff' for char in text)
        has_cyrillic = any('\u0400' <= char <= '\u04ff' for char in text)
        
        if has_chinese:
            return {
                "language": "zh",
                "is_english": False,
                "translated_text": text  # Would translate in real implementation
            }
        elif has_arabic:
            return {
                "language": "ar",
                "is_english": False,
                "translated_text": text
            }
        elif has_cyrillic:
            return {
                "language": "ru",
                "is_english": False,
                "translated_text": text
            }
        else:
            return {
                "language": "en",
                "is_english": True,
                "translated_text": text
            }


# Global mock instance
mock_enhancer = MockLLMEnhancer()
