# How Sentiment Analysis Works

## Problem Fixed ✅

**Issue:** Enhanced analysis showed wrong text ("terrible, worst, awful") instead of your actual input.

**Root Cause:** Docker container wasn't receiving Groq/Gemini API keys, so it fell back to mock enhancer with hardcoded responses.

**Solution:** Added API keys to `docker-compose.yml` environment variables and rebuilt container.

---

## How the Analysis Works Now

### 1. **Basic Sentiment Detection**
- **Model:** DistilBERT (Transformer-based NLP)
- **Process:** Analyzes entire text context, not just keywords
- **Output:** Sentiment (positive/negative) + Confidence (0-1 scale)

### 2. **Enhanced Analysis (LLM-Powered)**
When you enable "Enhanced Analysis":
- **Primary LLM:** Groq (llama-3.3-70b-versatile) - fast, accurate
- **Fallback:** Google Gemini (gemini-pro) if Groq fails
- **Receives:** Your actual input text + detected sentiment + confidence
- **Returns:** Context-specific explanation, key phrases, and recommendations

---

## Example: Mixed Sentiment

**Your Input:**
> "The new design is innovative, but the price is too high."

**Analysis Results:**
```json
{
  "sentiment": "negative",
  "confidence": 0.993,
  "probabilities": {
    "positive": 0.007,
    "negative": 0.993
  }
}
```

**Why Negative (Not Mixed)?**
1. **Transformer Context:** DistilBERT weighs the entire sentence structure
2. **Negation Detection:** The word "but" signals a contradiction, giving more weight to what follows
3. **Critical Pain Point:** "price is too high" is a **deal-breaker** phrase (blocks purchase decision)
4. **Positive Acknowledgment:** "innovative" is recognized but doesn't overcome the pricing concern

**Enhanced Explanation (LLM):**
- **Key Phrases:** "innovative", "too high", "price is too high"
- **Reasoning:** The word "too" emphasizes negativity; price is a critical decision factor
- **Recommendations:** 
  - Consider reducing the price
  - Offer discounts/promotions
  - Justify premium pricing with unique features
  - Explore tiered pricing models

---

## When Would It Be Mixed/Neutral?

**Balanced Example:**
> "The camera is excellent and battery lasts long, but it's a bit pricey."

**Analysis:**
```json
{
  "sentiment": "positive",
  "confidence": 0.65,
  "probabilities": {
    "positive": 0.65,
    "negative": 0.35
  }
}
```

**Why Positive (Low Confidence)?**
- Multiple strong positives ("excellent", "lasts long")
- Softened negative ("a bit pricey" vs "too high")
- Dashboard shows **Mixed Sentiment Alert** when difference <30%

---

## Dashboard Features

### Mixed Sentiment Detection
When probabilities are close (e.g., 55% positive, 45% negative):
```
⚠️ Mixed Sentiment Detected
This text contains balanced positive and negative elements (confidence difference <30%).
Consider breaking it into separate sentences for more granular analysis.
```

### Dynamic Analysis Sections
1. **💡 Detailed Explanation** - Why this sentiment was detected
2. **Key Phrases** - Specific words/phrases from YOUR input
3. **Recommendations** - Actionable suggestions based on YOUR content
4. **⚠️ Mixed Sentiment Alert** - Only shows when applicable to YOUR input

---

## How to Test

### Test 1: Strong Negative
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"This is terrible and disappointing","enhanced":true}'
```

**Expected:** High negative confidence, explanation mentions "terrible", "disappointing"

### Test 2: Strong Positive
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"Absolutely amazing product, love it!","enhanced":true}'
```

**Expected:** High positive confidence, explanation mentions "amazing", "love"

### Test 3: Balanced Mixed
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"Great features but poor battery life","enhanced":true}'
```

**Expected:** Close probabilities (50-70%), Mixed Sentiment Alert in dashboard

---

## Technical Architecture

```
User Input → API Endpoint
    ↓
Language Detection (if enhanced)
    ↓
DistilBERT Model → Sentiment + Confidence
    ↓
LLM Enhancement (Groq/Gemini) → Explanation + Context
    ↓
Response with:
    - Sentiment
    - Confidence
    - Probabilities
    - Enhanced Analysis (YOUR input-specific)
    - Key Phrases (from YOUR text)
    - Recommendations (tailored to YOUR content)
```

---

## Key Takeaways

1. **Not Just Keywords:** Transformer models understand context, negation, and sentence structure
2. **"But" Matters:** Phrases after "but" carry more weight in decision-making contexts
3. **Deal-Breakers Win:** Price complaints often override feature praise
4. **Confidence Scores:** Low confidence (50-70%) indicates mixed/neutral sentiment
5. **LLM Analysis:** Now shows YOUR actual input analysis, not hardcoded examples

---

## Access Your Dashboard

```bash
# Ensure services are running
docker-compose ps  # Check API (port 8000)
lsof -i:3000       # Check dashboard (port 3000)

# Open in browser
http://localhost:3000
```

Try the "innovative but expensive" example in the dashboard with enhanced analysis enabled!
