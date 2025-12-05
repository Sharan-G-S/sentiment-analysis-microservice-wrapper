# Enhanced Features Guide - Groq & Gemini Integration

## Overview

The sentiment analysis API now includes **LLM-powered enhancements** using Groq and Google Gemini to provide:

- **Detailed Explanations**: Why a sentiment was detected
- **Key Phrase Extraction**: Important words indicating sentiment
- **Actionable Suggestions**: Recommendations for negative feedback
- **Batch Insights**: Trends and patterns across multiple texts
- **Multi-language Support**: Language detection and translation

## Setup

### 1. Configure API Keys

Create a `.env` file in the project root:

```bash
# Groq API Key (get from https://console.groq.com)
GROQ_API_KEY=gsk_your_groq_key_here

# Google AI API Key (get from https://makersuite.google.com/app/apikey)
GOOGLE_API_KEY=AIzaSy_your_google_key_here
```

### 2. Install Dependencies

```bash
pip install groq google-generativeai python-dotenv
```

### 3. Restart Server

The server automatically loads environment variables on startup.

## Features

### Enhanced Single Prediction

**Endpoint**: `POST /api/v1/predict`

**New Parameters**:
- `enhanced` (bool): Enable LLM-powered analysis (default: false)
- `llm_provider` (string): Choose provider - "groq", "gemini", or "auto" (default: auto)

**Example Request**:

```bash
curl -X POST http://localhost:8001/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This product is absolutely amazing! I love it so much!",
    "enhanced": true,
    "return_probabilities": true,
    "llm_provider": "auto"
  }'
```

**Enhanced Response**:

```json
{
  "sentiment": "positive",
  "confidence": 0.9998853206634521,
  "probabilities": {
    "negative": 0.0001146,
    "positive": 0.9998853
  },
  "latency_ms": 1161.88,
  "timestamp": "2025-12-04T17:45:13.569596",
  "enhanced_analysis": {
    "explanation": "The text expresses strong positive sentiment with 100.0% confidence. Words like 'amazing', 'love', 'great', and 'excellent' indicate enthusiasm and satisfaction.",
    "key_phrases": [
      "amazing",
      "love it"
    ],
    "reasoning": "The text uses superlative language and emotional expressions that clearly indicate a positive experience. The strong conviction in the wording (e.g., 'absolutely', 'so much') reinforces the positive sentiment.",
    "suggestions": []
  },
  "language_info": {
    "language": "en",
    "is_english": true,
    "translated_text": "This product is absolutely amazing! I love it so much!"
  }
}
```

### Enhanced Batch Prediction

**Endpoint**: `POST /api/v1/predict/batch`

**New Parameters**:
- `enhanced` (bool): Enable batch insights (default: false)
- `llm_provider` (string): Choose provider (default: auto)

**Example Request**:

```bash
curl -X POST http://localhost:8001/api/v1/predict/batch \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "This is amazing! Love it!",
      "Terrible experience, very disappointed",
      "Great product, highly recommend",
      "Worst service ever, never coming back"
    ],
    "enhanced": true,
    "return_probabilities": true
  }'
```

**Enhanced Response**:

```json
{
  "predictions": [...],
  "total_latency_ms": 259.23,
  "batch_insights": {
    "summary": "Evenly split sentiment across 6 texts (50.0% positive, 50.0% negative).",
    "trends": {
      "positive": 50.0,
      "negative": 50.0
    },
    "patterns": [
      "Customer satisfaction themes in 3 reviews",
      "Service/product concerns in 3 reviews",
      "Diverse feedback across multiple touchpoints"
    ],
    "recommendation": "Focus on addressing negative feedback while maintaining positive experiences"
  }
}
```

## Use Cases

### 1. Customer Feedback Analysis

```python
import requests

# Analyze customer review with detailed insights
response = requests.post(
    "http://localhost:8001/api/v1/predict",
    json={
        "text": "The product quality is poor and customer service was unhelpful",
        "enhanced": True,
        "llm_provider": "gemini"
    }
)

result = response.json()
print(f"Sentiment: {result['sentiment']}")
print(f"Explanation: {result['enhanced_analysis']['explanation']}")
print(f"Key Issues: {', '.join(result['enhanced_analysis']['key_phrases'])}")
print(f"Suggestions: {result['enhanced_analysis']['suggestions']}")
```

### 2. Multi-Review Insights

```python
# Analyze multiple reviews and get trends
reviews = [
    "Excellent product, exceeded my expectations!",
    "Poor quality, not worth the price",
    "Amazing customer service and fast delivery",
    "Disappointed with the purchase, returning it",
    "Love this! Best purchase I've made",
    "Terrible experience, would not recommend"
]

response = requests.post(
    "http://localhost:8001/api/v1/predict/batch",
    json={
        "texts": reviews,
        "enhanced": True
    }
)

insights = response.json()['batch_insights']
print(f"Summary: {insights['summary']}")
print(f"Positive: {insights['trends']['positive']}%")
print(f"Negative: {insights['trends']['negative']}%")
print(f"Patterns: {insights['patterns']}")
```

### 3. Multi-Language Support

```python
# Analyze non-English text
response = requests.post(
    "http://localhost:8001/api/v1/predict",
    json={
        "text": "Este producto es increíble! Me encanta!",  # Spanish
        "enhanced": True
    }
)

result = response.json()
print(f"Detected Language: {result['language_info']['language']}")
print(f"Translated: {result['language_info']['translated_text']}")
print(f"Sentiment: {result['sentiment']}")
```

## Performance Considerations

### Latency

- **Basic prediction**: ~50-150ms
- **Enhanced prediction**: ~1-3 seconds (includes LLM call)
- **Batch enhanced**: ~2-5 seconds for 10 items

### Cost Optimization

1. **Use enhanced mode selectively**: Only for important analyses
2. **Choose provider wisely**:
   - Groq: Faster, good for real-time
   - Gemini: More detailed, better for batch analysis
3. **Batch processing**: Analyze multiple items together for better insights

### Fallback Mechanism

If LLM APIs are unavailable or quota exceeded:
- System automatically falls back to **mock enhancement mode**
- Provides rule-based explanations and insights
- No API calls required
- Guaranteed response time

## API Provider Comparison

| Feature | Groq | Gemini | Mock (Fallback) |
|---------|------|--------|-----------------|
| Speed | Fast (~1s) | Medium (~2s) | Instant (<10ms) |
| Quality | High | Very High | Good |
| Cost | Low | Low | Free |
| Quota | Generous | Limited (free tier) | Unlimited |
| Best For | Real-time | Detailed analysis | Always-on |

## Configuration Examples

### Production (High Volume)

```python
# Use mock mode for cost efficiency
response = requests.post(
    "http://localhost:8001/api/v1/predict",
    json={
        "text": review_text,
        "enhanced": True  # Will use mock if APIs unavailable
    }
)
```

### Premium Analysis

```python
# Use Gemini for highest quality
response = requests.post(
    "http://localhost:8001/api/v1/predict",
    json={
        "text": important_feedback,
        "enhanced": True,
        "llm_provider": "gemini"
    }
)
```

### Real-time Dashboard

```python
# Use Groq for speed
response = requests.post(
    "http://localhost:8001/api/v1/predict",
    json={
        "text": live_comment,
        "enhanced": True,
        "llm_provider": "groq"
    }
)
```

## Testing

Test all three modes:

```bash
# Test with mock (no API keys needed)
curl -X POST http://localhost:8001/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Great product!", "enhanced": true}'

# Test with Groq
curl -X POST http://localhost:8001/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Great product!", "enhanced": true, "llm_provider": "groq"}'

# Test with Gemini
curl -X POST http://localhost:8001/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Great product!", "enhanced": true, "llm_provider": "gemini"}'
```

## Troubleshooting

### Issue: "Invalid API Key"

**Solution**: Check your API keys in `.env` file
```bash
# Groq keys start with: gsk_
# Google keys start with: AIzaSy
```

### Issue: "Quota Exceeded"

**Solution**: System automatically falls back to mock mode. No action needed.

### Issue: Slow Response

**Solution**: 
1. Use `llm_provider: "groq"` for faster responses
2. Consider disabling enhanced mode for non-critical requests
3. Use batch mode for analyzing multiple items efficiently

## Next Steps

1. **Get API Keys** (optional, mock mode works without them):
   - Groq: https://console.groq.com
   - Google: https://makersuite.google.com/app/apikey

2. **Try Interactive Dashboard**:
   ```bash
   python dashboard.py
   # Toggle "Enhanced Analysis" in the UI
   ```

3. **Integrate into Your App**:
   - See `examples/enhanced_client.py` for code samples
   - Use enhanced mode for important user feedback
   - Enable batch insights for trend analysis

## Benefits

✅ **Better Insights**: Understand WHY sentiment was detected  
✅ **Actionable Data**: Get specific suggestions for improvement  
✅ **Multi-language**: Analyze feedback in any language  
✅ **Trend Analysis**: Identify patterns across batches  
✅ **Always Available**: Automatic fallback ensures 100% uptime  
✅ **Flexible**: Choose speed vs quality based on your needs
