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

    def analyze_news_importance_sync(self, headline: str, summary: str) -> dict:
        """
        Classify news importance and sentiment using Claude Haiku.
        Used specifically for notification filtering.

        Returns:
        {
            "importance": "high" | "medium" | "low",
            "sentiment": "bullish" | "bearish" | "neutral",
            "summary": "Brief explanation",
            "rationale": "Why this is important"
        }
        """
        try:
            message = self.client.messages.create(
                model=settings.CLAUDE_HAIKU_MODEL,
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Analyze this stock market news and classify its importance and sentiment.

Headline: {headline}
Summary: {summary}

Classification criteria:
- Importance: HIGH (material impact, earnings, M&A, regulatory), MEDIUM (notable but not critical), LOW (minor updates)
- Sentiment: BULLISH (positive for stock), BEARISH (negative), NEUTRAL

Return JSON: {{"importance": "...", "sentiment": "...", "summary": "...", "rationale": "..."}}

Only output valid JSON.""",
                    }
                ],
            )

            result = extract_json(message.content[0].text)
            return result
        except Exception as e:
            app_logger.error(f"AI news importance analysis error: {e}")
            return {
                "importance": "medium",
                "sentiment": "neutral",
                "summary": summary[:200] if summary else headline[:200],
                "rationale": "Analysis unavailable"
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

    def run_deep_dive_sync(self, ticker: str, profile: dict = None, financials: list = None) -> dict:
        """
        Generate comprehensive deep dive analysis for a specific stock.
        Uses available data from FMP plus AI knowledge.
        """
        # Build context from available data
        context_parts = [f"Ticker: {ticker}"]

        if profile:
            context_parts.append(f"Company: {profile.get('companyName', 'Unknown')}")
            context_parts.append(f"Sector: {profile.get('sector', 'Unknown')}")
            context_parts.append(f"Industry: {profile.get('industry', 'Unknown')}")
            context_parts.append(f"Description: {profile.get('description', 'N/A')}")
            if profile.get('mktCap'):
                context_parts.append(f"Market Cap: ${profile.get('mktCap', 0):,.0f}")
            if profile.get('price'):
                context_parts.append(f"Current Price: ${profile.get('price', 0):.2f}")

        if financials and len(financials) > 0:
            context_parts.append("\nRecent Financial Data:")
            for fin in financials[:3]:
                context_parts.append(f"- {fin.get('date', 'N/A')}: Revenue ${fin.get('revenue', 0):,.0f}, Net Income ${fin.get('netIncome', 0):,.0f}")

        context = "\n".join(context_parts)

        prompt = f"""You are a senior equity research analyst. Generate a comprehensive deep dive investment report for {ticker}.

## Available Data
{context}

## Task
Create a detailed investment analysis report. Use your knowledge about this company to provide insights even if the data above is limited.

## Required Output Format (JSON)

{{
    "report_metadata": {{
        "ticker": "{ticker}",
        "generated_at": "2026-01-07",
        "report_type": "deep_dive",
        "analyst_confidence": "high|medium|low"
    }},
    "company_overview": {{
        "name": "Full company name",
        "description": "2-3 sentence company description",
        "sector": "Sector",
        "industry": "Industry",
        "headquarters": "Location",
        "founded": "Year",
        "employees": "Approximate number",
        "website": "company website"
    }},
    "executive_summary": {{
        "investment_rating": "Strong Buy|Buy|Hold|Sell|Strong Sell",
        "price_target": "$XX.XX",
        "upside_potential": "XX%",
        "key_thesis": "2-3 sentence investment thesis",
        "risk_reward": "Favorable|Balanced|Unfavorable"
    }},
    "business_analysis": {{
        "business_model": "Description of how the company makes money",
        "revenue_streams": [
            {{"stream": "Revenue stream name", "percentage": "XX%", "growth_trend": "growing|stable|declining"}}
        ],
        "competitive_advantages": ["Advantage 1", "Advantage 2"],
        "market_position": "Description of market position",
        "key_products_services": ["Product/Service 1", "Product/Service 2"]
    }},
    "financial_analysis": {{
        "revenue_trend": "Description of revenue trajectory",
        "profitability": "Description of profitability metrics",
        "balance_sheet_health": "Strong|Moderate|Weak",
        "cash_flow_quality": "Description of cash flow",
        "key_metrics": {{
            "revenue_growth": "XX%",
            "gross_margin": "XX%",
            "operating_margin": "XX%",
            "net_margin": "XX%",
            "roe": "XX%",
            "debt_to_equity": "X.XX",
            "current_ratio": "X.XX",
            "pe_ratio": "XX.X",
            "ps_ratio": "XX.X",
            "ev_ebitda": "XX.X"
        }},
        "financial_outlook": "Description of financial outlook"
    }},
    "growth_drivers": [
        {{"driver": "Growth driver", "impact": "high|medium|low", "timeline": "near-term|medium-term|long-term", "description": "Details"}}
    ],
    "risk_factors": [
        {{"risk": "Risk factor", "severity": "high|medium|low", "probability": "high|medium|low", "mitigation": "How to mitigate"}}
    ],
    "competitive_landscape": {{
        "main_competitors": [
            {{"name": "Competitor", "ticker": "TICK", "comparison": "Brief comparison"}}
        ],
        "competitive_position": "Leader|Challenger|Follower|Niche",
        "barriers_to_entry": "High|Medium|Low",
        "threat_assessment": "Description of competitive threats"
    }},
    "valuation_analysis": {{
        "current_valuation": "Description of current valuation",
        "valuation_vs_peers": "Premium|In-line|Discount",
        "valuation_vs_history": "Above|At|Below historical average",
        "fair_value_estimate": "$XX.XX",
        "methodology": "Valuation methodology used",
        "key_assumptions": ["Assumption 1", "Assumption 2"]
    }},
    "catalysts": {{
        "near_term": [
            {{"catalyst": "Near-term catalyst", "expected_timing": "Q1 2026", "potential_impact": "Description"}}
        ],
        "long_term": [
            {{"catalyst": "Long-term catalyst", "expected_timing": "2026-2027", "potential_impact": "Description"}}
        ]
    }},
    "investment_recommendation": {{
        "summary": "Clear investment recommendation summary",
        "ideal_investor_profile": "Who should consider this stock",
        "position_sizing": "Core|Satellite|Speculative",
        "entry_strategy": "When/how to enter",
        "exit_triggers": ["Trigger 1", "Trigger 2"]
    }},
    "data_sources": [
        "Company SEC filings",
        "Earnings call transcripts",
        "Industry research",
        "Public financial databases"
    ],
    "disclaimers": "This analysis is for informational purposes only and does not constitute investment advice. Past performance is not indicative of future results."
}}

Provide realistic and specific data points. If you're uncertain about specific numbers, provide reasonable estimates based on the company's sector and size.

Only output valid JSON, no other text."""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=6000,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text
            app_logger.info(f"Deep dive response length: {len(response_text)}", extra={"response_length": len(response_text)})
            return extract_json(response_text)
        except Exception as e:
            app_logger.error(f"Error running AI deep dive: {e}", extra={"error": str(e)})
            return {"error": str(e)}

    def run_discovery_sync(self, theme: str, criteria: Optional[str] = None) -> dict:
        """
        Synchronous version for Celery tasks.
        Generates comprehensive investment research report.
        """
        # Parse criteria for report depth and other preferences
        report_depth = "standard"
        time_horizon = "medium"
        risk_tolerance = "moderate"

        if criteria:
            if "深度分析" in criteria or "comprehensive" in criteria.lower():
                report_depth = "comprehensive"
            elif "快速摘要" in criteria or "quick" in criteria.lower():
                report_depth = "quick"

            if "短期" in criteria or "short" in criteria.lower():
                time_horizon = "short"
            elif "长期" in criteria or "long" in criteria.lower():
                time_horizon = "long"

            if "保守" in criteria or "conservative" in criteria.lower():
                risk_tolerance = "conservative"
            elif "激进" in criteria or "aggressive" in criteria.lower():
                risk_tolerance = "aggressive"

        prompt = self._build_discovery_prompt(theme, criteria, report_depth, time_horizon, risk_tolerance)

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text
            app_logger.info(f"Discovery response length: {len(response_text)}", extra={"response_length": len(response_text)})
            return extract_json(response_text)
        except Exception as e:
            app_logger.error(f"Error running AI discovery: {e}", extra={"error": str(e)})
            return {"error": str(e)}

    def _build_discovery_prompt(self, theme: str, criteria: Optional[str], report_depth: str, time_horizon: str, risk_tolerance: str) -> str:
        """Build comprehensive discovery prompt based on user preferences"""

        base_prompt = f"""You are a senior equity research analyst at a top-tier investment bank. Your task is to create a comprehensive investment research report that a fund manager can directly reference for decision-making.

## Research Theme
{theme}

## User Preferences
- Investment Time Horizon: {time_horizon} (short=1-3 months, medium=6-12 months, long=1+ years)
- Risk Tolerance: {risk_tolerance} (conservative=blue-chip/low-vol, moderate=balanced, aggressive=high-growth/high-vol)
- Report Depth: {report_depth}
"""

        if criteria:
            base_prompt += f"""
## Additional Criteria from User
{criteria}
"""

        # Scoring criteria explanation
        scoring_criteria = """
## Scoring Methodology (1-100 scale)

For each stock, provide scores across these dimensions:

1. **Theme Alignment Score** (0-25 points): How well does the company fit the investment theme?
   - 20-25: Core player, directly addresses theme
   - 15-19: Strong relevance, significant exposure
   - 10-14: Moderate relevance, partial exposure
   - 0-9: Tangential connection

2. **Financial Health Score** (0-25 points): Based on balance sheet strength, profitability, cash flow
   - 20-25: Excellent financials, strong balance sheet, profitable
   - 15-19: Good financials, manageable debt, improving profitability
   - 10-14: Adequate financials, some concerns
   - 0-9: Weak financials, high risk

3. **Growth Potential Score** (0-25 points): Revenue growth, market expansion, competitive position
   - 20-25: Exceptional growth trajectory, market leader
   - 15-19: Strong growth, competitive advantages
   - 10-14: Moderate growth, stable position
   - 0-9: Slow growth or declining

4. **Valuation Score** (0-25 points): Relative to peers and growth (inverse - lower valuation = higher score)
   - 20-25: Significantly undervalued relative to growth
   - 15-19: Fairly valued with upside potential
   - 10-14: Full valuation, limited multiple expansion
   - 0-9: Overvalued, rich multiples
"""

        output_format = """
## Required Output Format (JSON)

You MUST respond with valid JSON in this exact structure:

{
    "report_metadata": {
        "generated_at": "2026-01-07",
        "theme": "The research theme",
        "time_horizon": "short|medium|long",
        "risk_profile": "conservative|moderate|aggressive",
        "analyst_confidence": "high|medium|low"
    },
    "executive_summary": {
        "overview": "2-3 paragraph executive summary of findings",
        "key_conclusion": "One sentence main takeaway",
        "top_picks": ["TICKER1", "TICKER2", "TICKER3"],
        "sector_outlook": "bullish|neutral|bearish",
        "market_conditions": "Brief assessment of current market environment for this theme"
    },
    "scoring_methodology": {
        "description": "Explain how stocks were scored",
        "dimensions": [
            {"name": "Theme Alignment", "weight": 25, "description": "How well company fits the theme"},
            {"name": "Financial Health", "weight": 25, "description": "Balance sheet, profitability, cash flow"},
            {"name": "Growth Potential", "weight": 25, "description": "Revenue growth, market expansion"},
            {"name": "Valuation", "weight": 25, "description": "Relative valuation vs peers and growth"}
        ]
    },
    "stocks": [
        {
            "ticker": "SYMBOL",
            "company_name": "Full Company Name",
            "sector": "Technology|Healthcare|etc",
            "market_cap": "$XXB",
            "overall_score": 85,
            "score_breakdown": {
                "theme_alignment": 23,
                "financial_health": 20,
                "growth_potential": 22,
                "valuation": 20
            },
            "recommendation": "Strong Buy|Buy|Hold|Sell",
            "price_target_upside": "XX%",
            "investment_thesis": "2-3 sentences on why to invest",
            "key_catalysts": [
                {"catalyst": "What could drive the stock", "timeline": "Q1 2026", "impact": "high|medium|low"}
            ],
            "strengths": [
                {"point": "Specific strength", "detail": "Supporting evidence or data"}
            ],
            "risks": [
                {"risk": "Specific risk", "severity": "high|medium|low", "mitigation": "How company/investor can mitigate"}
            ],
            "financial_metrics": {
                "revenue_growth_yoy": "XX%",
                "gross_margin": "XX%",
                "operating_margin": "XX%",
                "net_margin": "XX%",
                "pe_ratio": "XX.X",
                "ps_ratio": "XX.X",
                "debt_to_equity": "X.XX",
                "free_cash_flow": "$XXM",
                "roe": "XX%"
            },
            "competitive_position": {
                "market_share": "XX%",
                "key_competitors": ["Competitor1", "Competitor2"],
                "competitive_moat": "Description of competitive advantages"
            },
            "recent_developments": [
                "Recent news or development that's relevant"
            ]
        }
    ],
    "sector_analysis": {
        "industry_overview": "Overview of the sector/industry",
        "market_size": "Total addressable market size",
        "growth_drivers": ["Driver 1", "Driver 2"],
        "headwinds": ["Headwind 1", "Headwind 2"],
        "competitive_landscape": "Description of competitive dynamics"
    },
    "risk_matrix": {
        "macro_risks": [
            {"risk": "Macro risk", "probability": "high|medium|low", "impact": "high|medium|low"}
        ],
        "sector_risks": [
            {"risk": "Sector-specific risk", "probability": "high|medium|low", "impact": "high|medium|low"}
        ],
        "execution_risks": [
            {"risk": "Execution risk", "probability": "high|medium|low", "impact": "high|medium|low"}
        ]
    },
    "data_sources": [
        "Company SEC filings (10-K, 10-Q)",
        "Earnings call transcripts",
        "Industry reports",
        "Financial data providers"
    ],
    "disclaimers": "This research is for informational purposes only and does not constitute investment advice. Past performance is not indicative of future results. Always conduct your own due diligence."
}

## Important Guidelines

1. Identify 5-8 stocks that best fit the theme
2. All financial metrics should be realistic and based on typical ranges for each sector
3. Provide specific, actionable insights rather than generic statements
4. Be honest about risks and limitations
5. Tailor recommendations to the specified time horizon and risk tolerance
6. Include specific catalysts with timelines
7. Ensure scoring is consistent and defensible

Only output valid JSON, no other text before or after.
"""

        return base_prompt + scoring_criteria + output_format

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
        Uses the same comprehensive prompt as sync version.
        """
        # Parse criteria for report depth and other preferences
        report_depth = "standard"
        time_horizon = "medium"
        risk_tolerance = "moderate"

        if criteria:
            if "深度分析" in criteria or "comprehensive" in criteria.lower():
                report_depth = "comprehensive"
            elif "快速摘要" in criteria or "quick" in criteria.lower():
                report_depth = "quick"

            if "短期" in criteria or "short" in criteria.lower():
                time_horizon = "short"
            elif "长期" in criteria or "long" in criteria.lower():
                time_horizon = "long"

            if "保守" in criteria or "conservative" in criteria.lower():
                risk_tolerance = "conservative"
            elif "激进" in criteria or "aggressive" in criteria.lower():
                risk_tolerance = "aggressive"

        prompt = self._build_discovery_prompt(theme, criteria, report_depth, time_horizon, risk_tolerance)

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}],
            )

            import json
            return json.loads(message.content[0].text)
        except Exception as e:
            app_logger.error(f"Error running AI discovery: {e}", extra={"error": str(e)})
            return {"error": str(e)}


ai_service = AIService()
