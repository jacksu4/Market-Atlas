from datetime import datetime, timezone
from typing import List, Optional
import httpx
import re
from bs4 import BeautifulSoup

from app.core.config import settings


class SECService:
    BASE_URL = "https://data.sec.gov"
    EDGAR_URL = "https://www.sec.gov/cgi-bin/browse-edgar"
    USER_AGENT = "Market-Atlas research@example.com"

    # ==================== SYNC METHODS (for Celery) ====================

    def get_recent_filings_sync(self, cik: str, filing_types: Optional[List[str]] = None) -> List[dict]:
        """Synchronous version for Celery tasks"""
        if not cik:
            return []

        cik = cik.zfill(10)

        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.BASE_URL}/submissions/CIK{cik}.json",
                    headers={"User-Agent": self.USER_AGENT},
                    timeout=15.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    filings = data.get("filings", {}).get("recent", {})

                    results = []
                    forms = filings.get("form", [])
                    accession_numbers = filings.get("accessionNumber", [])
                    filing_dates = filings.get("filingDate", [])
                    primary_documents = filings.get("primaryDocument", [])

                    for i in range(len(forms)):
                        form = forms[i]

                        if filing_types and form not in filing_types:
                            continue

                        accession = accession_numbers[i].replace("-", "")
                        filing_date = filing_dates[i]
                        primary_doc = primary_documents[i] if i < len(primary_documents) else ""

                        results.append({
                            "form": form,
                            "accession_number": accession_numbers[i],
                            "filing_date": filing_date,
                            "filing_url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary_doc}",
                            "index_url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/",
                        })

                        if len(results) >= 50:
                            break

                    return results
        except Exception as e:
            print(f"Error fetching SEC filings for CIK {cik}: {e}")

        return []

    def get_filing_text_sync(self, filing_url: str) -> Optional[str]:
        """Synchronous version for Celery tasks"""
        try:
            with httpx.Client() as client:
                response = client.get(
                    filing_url,
                    headers={"User-Agent": self.USER_AGENT},
                    timeout=30.0,
                    follow_redirects=True,
                )

                if response.status_code == 200:
                    content = response.text

                    if "<html" in content.lower():
                        # Use BeautifulSoup for safe HTML parsing
                        soup = BeautifulSoup(content, "lxml")
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        # Get text and normalize whitespace
                        content = soup.get_text(separator=" ", strip=True)
                        content = re.sub(r"\s+", " ", content)

                    return content.strip()
        except Exception as e:
            print(f"Error fetching filing text from {filing_url}: {e}")

        return None

    # ==================== ASYNC METHODS (for FastAPI) ====================

    async def get_recent_filings(self, cik: str, filing_types: Optional[List[str]] = None) -> List[dict]:
        """
        Get recent filings for a company by CIK.
        filing_types: ["10-K", "10-Q", "8-K", etc.]
        """
        if not cik:
            return []

        # Ensure CIK is 10 digits with leading zeros
        cik = cik.zfill(10)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/submissions/CIK{cik}.json",
                    headers={"User-Agent": self.USER_AGENT},
                    timeout=15.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    filings = data.get("filings", {}).get("recent", {})

                    results = []
                    forms = filings.get("form", [])
                    accession_numbers = filings.get("accessionNumber", [])
                    filing_dates = filings.get("filingDate", [])
                    primary_documents = filings.get("primaryDocument", [])

                    for i in range(len(forms)):
                        form = forms[i]

                        # Filter by filing type if specified
                        if filing_types and form not in filing_types:
                            continue

                        accession = accession_numbers[i].replace("-", "")
                        filing_date = filing_dates[i]
                        primary_doc = primary_documents[i] if i < len(primary_documents) else ""

                        results.append({
                            "form": form,
                            "accession_number": accession_numbers[i],
                            "filing_date": filing_date,
                            "filing_url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary_doc}",
                            "index_url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/",
                        })

                        if len(results) >= 50:
                            break

                    return results
        except Exception as e:
            print(f"Error fetching SEC filings for CIK {cik}: {e}")

        return []

    async def get_filing_text(self, filing_url: str) -> Optional[str]:
        """
        Download and extract text from a filing document.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    filing_url,
                    headers={"User-Agent": self.USER_AGENT},
                    timeout=30.0,
                    follow_redirects=True,
                )

                if response.status_code == 200:
                    content = response.text

                    # If HTML, strip tags
                    if "<html" in content.lower():
                        # Use BeautifulSoup for safe HTML parsing
                        soup = BeautifulSoup(content, "lxml")
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        # Get text and normalize whitespace
                        content = soup.get_text(separator=" ", strip=True)
                        content = re.sub(r"\s+", " ", content)

                    return content.strip()
        except Exception as e:
            print(f"Error fetching filing text from {filing_url}: {e}")

        return None

    async def search_filings_by_ticker(
        self,
        ticker: str,
        filing_type: Optional[str] = None,
        count: int = 20,
    ) -> List[dict]:
        """
        Search for filings by ticker symbol.
        """
        params = {
            "action": "getcompany",
            "CIK": ticker,
            "type": filing_type or "",
            "dateb": "",
            "owner": "include",
            "count": str(count),
            "output": "atom",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.EDGAR_URL,
                    params=params,
                    headers={"User-Agent": self.USER_AGENT},
                    timeout=15.0,
                )

                if response.status_code == 200:
                    # Parse Atom feed (simplified)
                    content = response.text
                    entries = re.findall(r"<entry>(.*?)</entry>", content, re.DOTALL)

                    results = []
                    for entry in entries:
                        title_match = re.search(r"<title>(.*?)</title>", entry)
                        link_match = re.search(r'<link href="([^"]+)"', entry)
                        updated_match = re.search(r"<updated>(.*?)</updated>", entry)

                        if title_match and link_match:
                            results.append({
                                "title": title_match.group(1),
                                "url": link_match.group(1),
                                "date": updated_match.group(1) if updated_match else None,
                            })

                    return results
        except Exception as e:
            print(f"Error searching SEC filings for {ticker}: {e}")

        return []


sec_service = SECService()
