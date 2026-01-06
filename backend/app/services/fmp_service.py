from typing import List, Optional
import httpx

from app.core.config import settings


class FMPService:
    """Financial Modeling Prep API Service"""

    BASE_URL = "https://financialmodelingprep.com/api"

    def __init__(self):
        self.api_key = settings.FMP_API_KEY

    # ==================== SYNC METHODS (for Celery) ====================

    def get_earnings_transcript_sync(
        self,
        ticker: str,
        year: Optional[int] = None,
        quarter: Optional[int] = None,
    ) -> Optional[dict]:
        """Synchronous version for Celery tasks"""
        if not self.api_key:
            return None

        try:
            params = {"apikey": self.api_key}

            if year and quarter:
                url = f"{self.BASE_URL}/v3/earning_call_transcript/{ticker.upper()}"
                params["year"] = year
                params["quarter"] = quarter
            else:
                url = f"{self.BASE_URL}/v4/batch_earning_call_transcript/{ticker.upper()}"

            with httpx.Client() as client:
                response = client.get(url, params=params, timeout=30.0)

                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        return data[0]
                    elif isinstance(data, dict):
                        return data
        except Exception as e:
            print(f"Error fetching earnings transcript for {ticker}: {e}")

        return None

    def get_all_transcripts_sync(self, ticker: str, limit: int = 4) -> List[dict]:
        """Synchronous version for Celery tasks"""
        if not self.api_key:
            return []

        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.BASE_URL}/v4/batch_earning_call_transcript/{ticker.upper()}",
                    params={"apikey": self.api_key},
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        return data[:limit]
        except Exception as e:
            print(f"Error fetching earnings transcripts for {ticker}: {e}")

        return []

    def get_company_profile_sync(self, ticker: str) -> Optional[dict]:
        """Synchronous version for Celery tasks"""
        if not self.api_key:
            return None

        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.BASE_URL}/v3/profile/{ticker.upper()}",
                    params={"apikey": self.api_key},
                    timeout=15.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        return data[0]
        except Exception as e:
            print(f"Error fetching company profile for {ticker}: {e}")

        return None

    def get_income_statement_sync(self, ticker: str, period: str = "annual", limit: int = 5) -> List[dict]:
        """Synchronous version for Celery tasks"""
        if not self.api_key:
            return []

        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.BASE_URL}/v3/income-statement/{ticker.upper()}",
                    params={
                        "period": period,
                        "limit": limit,
                        "apikey": self.api_key,
                    },
                    timeout=15.0,
                )

                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"Error fetching income statement for {ticker}: {e}")

        return []

    # ==================== ASYNC METHODS (for FastAPI) ====================

    async def get_earnings_transcript(
        self,
        ticker: str,
        year: Optional[int] = None,
        quarter: Optional[int] = None,
    ) -> Optional[dict]:
        """
        Get earnings call transcript for a specific quarter.
        """
        if not self.api_key:
            return None

        try:
            params = {"apikey": self.api_key}

            if year and quarter:
                url = f"{self.BASE_URL}/v3/earning_call_transcript/{ticker.upper()}"
                params["year"] = year
                params["quarter"] = quarter
            else:
                # Get most recent
                url = f"{self.BASE_URL}/v4/batch_earning_call_transcript/{ticker.upper()}"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=30.0)

                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        return data[0]
                    elif isinstance(data, dict):
                        return data
        except Exception as e:
            print(f"Error fetching earnings transcript for {ticker}: {e}")

        return None

    async def get_all_transcripts(self, ticker: str, limit: int = 4) -> List[dict]:
        """
        Get multiple recent earnings call transcripts.
        """
        if not self.api_key:
            return []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/v4/batch_earning_call_transcript/{ticker.upper()}",
                    params={"apikey": self.api_key},
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        return data[:limit]
        except Exception as e:
            print(f"Error fetching earnings transcripts for {ticker}: {e}")

        return []

    async def get_company_profile(self, ticker: str) -> Optional[dict]:
        """
        Get company profile information.
        """
        if not self.api_key:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/v3/profile/{ticker.upper()}",
                    params={"apikey": self.api_key},
                    timeout=15.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        return data[0]
        except Exception as e:
            print(f"Error fetching company profile for {ticker}: {e}")

        return None

    async def get_income_statement(self, ticker: str, period: str = "annual", limit: int = 5) -> List[dict]:
        """
        Get income statements.
        period: "annual" or "quarter"
        """
        if not self.api_key:
            return []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/v3/income-statement/{ticker.upper()}",
                    params={
                        "period": period,
                        "limit": limit,
                        "apikey": self.api_key,
                    },
                    timeout=15.0,
                )

                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"Error fetching income statement for {ticker}: {e}")

        return []

    async def get_stock_screener(
        self,
        market_cap_min: Optional[int] = None,
        market_cap_max: Optional[int] = None,
        sector: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 100,
    ) -> List[dict]:
        """
        Screen stocks by various criteria.
        """
        if not self.api_key:
            return []

        params = {"apikey": self.api_key, "limit": limit}

        if market_cap_min:
            params["marketCapMoreThan"] = market_cap_min
        if market_cap_max:
            params["marketCapLowerThan"] = market_cap_max
        if sector:
            params["sector"] = sector
        if industry:
            params["industry"] = industry

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/v3/stock-screener",
                    params=params,
                    timeout=30.0,
                )

                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"Error running stock screener: {e}")

        return []


fmp_service = FMPService()
