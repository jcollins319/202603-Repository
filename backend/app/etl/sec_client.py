import logging
import time

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

SEC_BASE_URL = "https://www.sec.gov"
SEC_EDGAR_FULL_INDEX = "https://www.sec.gov/Archives/edgar/full-index"
SEC_EFTS_URL = "https://efts.sec.gov/LATEST/search-index"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions"

# SEC rate limit: max 10 requests per second
REQUEST_DELAY = 0.15


class SECClient:
    def __init__(self):
        self.client = httpx.Client(
            headers={"User-Agent": settings.sec_user_agent},
            timeout=30.0,
            follow_redirects=True,
        )
        self._last_request_time = 0.0

    def _rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
        self._last_request_time = time.time()

    def get(self, url: str) -> httpx.Response:
        self._rate_limit()
        logger.debug("GET %s", url)
        response = self.client.get(url)
        response.raise_for_status()
        return response

    def get_recent_form4_filings(self, start: int = 0, count: int = 40) -> dict:
        """Fetch recent Form 4 filings from SEC EDGAR full-text search."""
        url = "https://efts.sec.gov/LATEST/search-index"
        params = {
            "q": '"Form 4"',
            "dateRange": "custom",
            "forms": "4",
            "startdt": "",
            "enddt": "",
            "start": start,
            "count": count,
        }
        # Use the EDGAR full-text search API
        search_url = "https://efts.sec.gov/LATEST/search-index"
        self._rate_limit()
        try:
            response = self.client.get(
                "https://efts.sec.gov/LATEST/search-index",
                params={"q": '"Form 4"', "forms": "4", "start": start, "count": count},
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            logger.exception("Failed to fetch recent Form 4 filings from EFTS")
            return {"hits": {"hits": []}}

    def get_recent_filings_rss(self) -> str:
        """Fetch the SEC EDGAR RSS feed for recent Form 4 filings."""
        url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&dateb=&owner=include&count=40&search_text=&start=0&output=atom"
        response = self.get(url)
        return response.text

    def get_filing_document(self, accession_url: str) -> str:
        """Fetch a specific filing document (XML)."""
        response = self.get(accession_url)
        return response.text

    def get_company_submissions(self, cik: str) -> dict:
        """Fetch company submission data from SEC."""
        cik_padded = cik.zfill(10)
        url = f"{SEC_SUBMISSIONS_URL}/CIK{cik_padded}.json"
        response = self.get(url)
        return response.json()

    def get_daily_index(self, year: int, quarter: int) -> str:
        """Fetch the daily index for a specific quarter."""
        url = f"{SEC_EDGAR_FULL_INDEX}/{year}/QTR{quarter}/form.idx"
        response = self.get(url)
        return response.text

    def close(self):
        self.client.close()


sec_client = SECClient()
