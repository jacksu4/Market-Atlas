from typing import Optional
import re
import json
import anthropic

from app.core.config import settings
from app.core.logging_config import app_logger
from app.models.news import NewsSentiment, NewsImportance


def extract_json(text: str) -> dict:
    """Extract JSON from text, handling markdown code blocks"""
    # Try to find JSON in code blocks
    code_block_pattern = r'```(?:json)?\s*([\s\S]*?)```'
    matches = re.findall(code_block_pattern, text)
    if matches:
        text = matches[0].strip()

    # Try to find JSON object pattern
    json_pattern = r'\{[\s\S]*\}'
    match = re.search(json_pattern, text)
    if match:
        text = match.group()

    return json.loads(text)


class AIService:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # ==================== SYNC METHODS (for Celery) ====================

    def analyze_news_sync(self, headline: str, summary: Optional[str] = None) -> dict:
        """Synchronous version for Celery tasks"""
        content = f"Headline: {headline}"
        if summary:
            content += f"\n\nSummary: {summary}"

        try:
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Analyze this financial news article for an investor. Be concise.

{content}

Respond in JSON format:
{{
    "sentiment": "bullish" | "bearish" | "neutral",
    "importance": "high" | "medium" | "low",
    "key_points": ["point1", "point2"],
    "ai_summary": "One sentence summary for investor"
}}

Only output valid JSON, no other text.""",
                    }
                ],
            )

            result = extract_json(message.content[0].text)

            return {
                "sentiment": NewsSentiment(result.get("sentiment", "neutral")),
                "importance": NewsImportance(result.get("importance", "medium")),
                "key_points": result.get("key_points", []),
                "ai_summary": result.get("ai_summary", ""),
            }
        except Exception as e:
            app_logger.error(f"Error analyzing news with AI: {e}", extra={"error": str(e)})
            return {
                "sentiment": NewsSentiment.NEUTRAL,
                "importance": NewsImportance.MEDIUM,
                "key_points": [],
                "ai_summary": "",
            }

    def analyze_sec_filing_sync(self, filing_type: str, text: str, ticker: str) -> dict:
        """Synchronous version for Celery tasks"""
        max_chars = 150000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[Content truncated due to length...]"

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[
                    {
                        "role": "user",
                        "content": f"""You are a senior financial analyst. Analyze this {filing_type} filing for {ticker}.

{text}

Provide a comprehensive analysis in JSON format:
{{
    "summary": "Executive summary (2-3 paragraphs)",
    "key_financials": {{
        "revenue": "...",
        "net_income": "...",
        "eps": "...",
        "guidance": "..."
    }},
    "risk_factors_changes": ["Notable changes in risk factors"],
    "mda_highlights": ["Key points from Management Discussion & Analysis"],
    "notable_changes": ["Significant changes from previous period"],
    "investment_implications": ["Key takeaways for investors"],
    "sentiment": "bullish" | "bearish" | "neutral"
}}

Only output valid JSON.""",
                    }
                ],
            )

            return extract_json(message.content[0].text)
        except Exception as e:
            app_logger.error(f"Error analyzing SEC filing with AI: {e}", extra={"error": str(e)})
            return {"error": str(e)}

    def analyze_earnings_call_sync(self, transcript: str, ticker: str, quarter: str) -> dict:
        """Synchronous version for Celery tasks"""
        max_chars = 150000
        if len(transcript) > max_chars:
            transcript = transcript[:max_chars] + "\n\n[Transcript truncated...]"

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Analyze this {quarter} earnings call transcript for {ticker}.

{transcript}

Provide analysis in JSON format:
{{
    "summary": "Executive summary of the call",
    "management_tone": "optimistic" | "cautious" | "defensive" | "confident",
    "key_metrics": {{
        "revenue": "...",
        "guidance": "...",
        "margins": "..."
    }},
    "guidance_changes": ["Changes in forward guidance"],
    "analyst_concerns": ["Key concerns raised by analysts"],
    "management_responses": ["Notable management responses"],
    "key_quotes": ["Important direct quotes"],
    "investment_implications": ["Takeaways for investors"],
    "sentiment": "bullish" | "bearish" | "neutral"
}}

Only output valid JSON.""",
                    }
                ],
            )

            return extract_json(message.content[0].text)
        except Exception as e:
            app_logger.error(f"Error analyzing earnings call with AI: {e}", extra={"error": str(e)})
            return {"error": str(e)}

    def run_discovery_sync(self, theme: str, criteria: Optional[str] = None) -> dict:
        """Synchronous version for Celery tasks"""
        prompt = f"""You are a senior equity research analyst specializing in technology stocks.

Research Theme: {theme}
"""
        if criteria:
            prompt += f"\nAdditional Criteria: {criteria}\n"

        prompt += """
Based on your knowledge, identify 5-10 US-listed stocks that best fit this investment theme.

For each stock, provide:
1. Ticker symbol
2. Company name
3. Why it fits the theme (2-3 sentences)
4. Key investment thesis
5. Potential risks
6. Confidence score (1-100)

Respond in JSON format:
{
    "methodology": "Brief description of your research approach",
    "candidates": [
        {
            "ticker": "SYMBOL",
            "company_name": "Full Company Name",
            "theme_fit": "Why this company fits the theme",
            "investment_thesis": "Key investment thesis",
            "risks": ["Risk 1", "Risk 2"],
            "confidence_score": 85
        }
    ],
    "market_overview": "Brief overview of the theme/sector"
}

Only output valid JSON."""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text
            app_logger.info(f"Discovery response length: {len(response_text)}", extra={"response_length": len(response_text)})
            return extract_json(response_text)
        except Exception as e:
            app_logger.error(f"Error running AI discovery: {e}", extra={"error": str(e)})
            return {"error": str(e)}

    # ==================== ASYNC METHODS (for FastAPI) ====================

    async def analyze_news(self, headline: str, summary: Optional[str] = None) -> dict:
        """
        Analyze a news item using Claude Haiku for speed.
        Returns sentiment, importance, and key points.
        """
        content = f"Headline: {headline}"
        if summary:
            content += f"\n\nSummary: {summary}"

        try:
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Analyze this financial news article for an investor. Be concise.

{content}

Respond in JSON format:
{{
    "sentiment": "bullish" | "bearish" | "neutral",
    "importance": "high" | "medium" | "low",
    "key_points": ["point1", "point2"],
    "ai_summary": "One sentence summary for investor"
}}

Only output valid JSON, no other text.""",
                    }
                ],
            )

            import json
            result = json.loads(message.content[0].text)

            return {
                "sentiment": NewsSentiment(result.get("sentiment", "neutral")),
                "importance": NewsImportance(result.get("importance", "medium")),
                "key_points": result.get("key_points", []),
                "ai_summary": result.get("ai_summary", ""),
            }
        except Exception as e:
            app_logger.error(f"Error analyzing news with AI: {e}", extra={"error": str(e)})
            return {
                "sentiment": NewsSentiment.NEUTRAL,
                "importance": NewsImportance.MEDIUM,
                "key_points": [],
                "ai_summary": "",
            }

    async def analyze_sec_filing(self, filing_type: str, text: str, ticker: str) -> dict:
        """
        Analyze SEC filing using Claude Sonnet for deep analysis.
        """
        # Truncate text if too long (Claude has context limits)
        max_chars = 150000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[Content truncated due to length...]"

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[
                    {
                        "role": "user",
                        "content": f"""You are a senior financial analyst. Analyze this {filing_type} filing for {ticker}.

{text}

Provide a comprehensive analysis in JSON format:
{{
    "summary": "Executive summary (2-3 paragraphs)",
    "key_financials": {{
        "revenue": "...",
        "net_income": "...",
        "eps": "...",
        "guidance": "..."
    }},
    "risk_factors_changes": ["Notable changes in risk factors"],
    "mda_highlights": ["Key points from Management Discussion & Analysis"],
    "notable_changes": ["Significant changes from previous period"],
    "investment_implications": ["Key takeaways for investors"],
    "sentiment": "bullish" | "bearish" | "neutral"
}}

Only output valid JSON.""",
                    }
                ],
            )

            import json
            return json.loads(message.content[0].text)
        except Exception as e:
            app_logger.error(f"Error analyzing SEC filing with AI: {e}", extra={"error": str(e)})
            return {"error": str(e)}

    async def analyze_earnings_call(self, transcript: str, ticker: str, quarter: str) -> dict:
        """
        Analyze earnings call transcript using Claude Sonnet.
        """
        max_chars = 150000
        if len(transcript) > max_chars:
            transcript = transcript[:max_chars] + "\n\n[Transcript truncated...]"

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Analyze this {quarter} earnings call transcript for {ticker}.

{transcript}

Provide analysis in JSON format:
{{
    "summary": "Executive summary of the call",
    "management_tone": "optimistic" | "cautious" | "defensive" | "confident",
    "key_metrics": {{
        "revenue": "...",
        "guidance": "...",
        "margins": "..."
    }},
    "guidance_changes": ["Changes in forward guidance"],
    "analyst_concerns": ["Key concerns raised by analysts"],
    "management_responses": ["Notable management responses"],
    "key_quotes": ["Important direct quotes"],
    "investment_implications": ["Takeaways for investors"],
    "sentiment": "bullish" | "bearish" | "neutral"
}}

Only output valid JSON.""",
                    }
                ],
            )

            import json
            return json.loads(message.content[0].text)
        except Exception as e:
            app_logger.error(f"Error analyzing earnings call with AI: {e}", extra={"error": str(e)})
            return {"error": str(e)}

    async def run_discovery(self, theme: str, criteria: Optional[str] = None) -> dict:
        """
        Run AI discovery to find potential investment targets.
        """
        prompt = f"""You are a senior equity research analyst specializing in technology stocks.

Research Theme: {theme}
"""
        if criteria:
            prompt += f"\nAdditional Criteria: {criteria}\n"

        prompt += """
Based on your knowledge, identify 5-10 US-listed stocks that best fit this investment theme.

For each stock, provide:
1. Ticker symbol
2. Company name
3. Why it fits the theme (2-3 sentences)
4. Key investment thesis
5. Potential risks
6. Confidence score (1-100)

Respond in JSON format:
{
    "methodology": "Brief description of your research approach",
    "candidates": [
        {
            "ticker": "SYMBOL",
            "company_name": "Full Company Name",
            "theme_fit": "Why this company fits the theme",
            "investment_thesis": "Key investment thesis",
            "risks": ["Risk 1", "Risk 2"],
            "confidence_score": 85
        }
    ],
    "market_overview": "Brief overview of the theme/sector"
}

Only output valid JSON."""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )

            import json
            return json.loads(message.content[0].text)
        except Exception as e:
            app_logger.error(f"Error running AI discovery: {e}", extra={"error": str(e)})
            return {"error": str(e)}


ai_service = AIService()
