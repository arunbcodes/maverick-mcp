"""
Structured prompts for conference call analysis.

This module contains prompt templates for AI-powered analysis of earnings call transcripts.
Prompts are designed for structured output with JSON responses.
"""

SUMMARIZATION_PROMPT = """You are a financial analyst expert specializing in earnings call analysis.
Your task is to analyze the provided conference call transcript and generate a comprehensive, structured summary.

**TRANSCRIPT:**
{transcript_text}

**COMPANY INFORMATION:**
- Ticker: {ticker}
- Company: {company_name}
- Quarter: {quarter}
- Fiscal Year: {fiscal_year}

**INSTRUCTIONS:**
Analyze the transcript thoroughly and provide a structured JSON response with the following sections:

1. **executive_summary**: A concise 2-3 sentence overview of the key takeaways from the call.

2. **key_metrics**: Extract and summarize financial metrics discussed:
   - revenue: Revenue figures and growth rates
   - profit: Profit/earnings figures (net income, EPS, etc.)
   - margins: Profit margins, operating margins
   - growth_rates: YoY or QoQ growth percentages
   - guidance: Any forward-looking financial guidance
   - other_metrics: Other important KPIs mentioned

3. **business_highlights**: List 3-5 major business developments, initiatives, or achievements discussed.

4. **management_guidance**: Extract forward-looking statements and guidance:
   - revenue_guidance: Future revenue expectations
   - earnings_guidance: Future earnings expectations
   - strategic_initiatives: Planned initiatives or investments
   - market_outlook: Management's view on market conditions

5. **sentiment**: Overall sentiment of the call (one of: "very_positive", "positive", "neutral", "cautious", "negative")
   - Include a brief explanation for the sentiment classification

6. **key_risks**: List 3-5 risks or challenges discussed by management.

7. **opportunities**: List 3-5 opportunities or growth drivers mentioned.

8. **qa_insights**: Key insights from the Q&A session (if present):
   - Most discussed topics
   - Any surprising questions or revelations
   - Management's confidence level in responses

9. **market_context**: Any discussion of:
   - Competitive landscape
   - Industry trends
   - Macroeconomic factors
   - Regulatory environment

10. **analyst_focus**: Topics that analysts were most interested in during Q&A.

**OUTPUT FORMAT:**
Respond ONLY with valid JSON. Do not include any additional text, markdown, or formatting.

Example structure:
{{
  "executive_summary": "...",
  "key_metrics": {{
    "revenue": "...",
    "profit": "...",
    "margins": "...",
    "growth_rates": "...",
    "guidance": "...",
    "other_metrics": "..."
  }},
  "business_highlights": ["...", "...", "..."],
  "management_guidance": {{
    "revenue_guidance": "...",
    "earnings_guidance": "...",
    "strategic_initiatives": "...",
    "market_outlook": "..."
  }},
  "sentiment": "positive",
  "sentiment_explanation": "...",
  "key_risks": ["...", "...", "..."],
  "opportunities": ["...", "...", "..."],
  "qa_insights": {{
    "most_discussed": ["...", "..."],
    "surprises": "...",
    "confidence_level": "high/medium/low"
  }},
  "market_context": {{
    "competitive_landscape": "...",
    "industry_trends": "...",
    "macroeconomic_factors": "...",
    "regulatory_environment": "..."
  }},
  "analyst_focus": ["...", "...", "..."]
}}

Analyze the transcript now and provide the JSON response:"""


SENTIMENT_ANALYSIS_PROMPT = """You are a financial sentiment analysis expert. Analyze the provided earnings call transcript and determine the overall sentiment.

**TRANSCRIPT:**
{transcript_text}

**INSTRUCTIONS:**
1. Analyze the tone and content of management's statements
2. Consider financial performance relative to expectations
3. Evaluate guidance and forward-looking statements
4. Assess management confidence and clarity
5. Consider analyst reactions during Q&A

**SENTIMENT CATEGORIES:**
- very_positive: Exceptional results, strong growth, confident outlook
- positive: Good results, solid performance, optimistic outlook
- neutral: Mixed results, balanced perspective, cautious outlook
- cautious: Challenges mentioned, uncertain outlook, defensive tone
- negative: Poor results, significant challenges, pessimistic outlook

**OUTPUT FORMAT:**
Respond with ONLY valid JSON:
{{
  "sentiment": "positive",
  "confidence_score": 0.85,
  "explanation": "Management expressed strong confidence with revenue beating expectations by 15%. Guidance was raised for next quarter. Tone was optimistic throughout.",
  "key_positive_signals": ["Revenue beat", "Guidance raise", "Confident tone"],
  "key_negative_signals": ["Margin compression", "Supply chain concerns"],
  "management_confidence": "high",
  "analyst_sentiment": "positive"
}}

Analyze the sentiment now:"""


# Token limits for different summarization modes
SUMMARIZATION_MODES = {
    "concise": {
        "max_tokens": 1500,
        "temperature": 0.2,
        "description": "Brief summary focusing on key metrics and highlights",
    },
    "standard": {
        "max_tokens": 3000,
        "temperature": 0.3,
        "description": "Comprehensive summary with detailed analysis",
    },
    "detailed": {
        "max_tokens": 5000,
        "temperature": 0.3,
        "description": "Extensive summary with deep insights and context",
    },
}
