import logging
import re
from dataclasses import dataclass, field
from datetime import datetime

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ParsedTransaction:
    issuer_name: str = ""
    issuer_ticker: str = ""
    issuer_cik: str = ""
    insider_name: str = ""
    insider_cik: str = ""
    insider_title: str = ""
    is_director: bool = False
    is_officer: bool = False
    is_ten_percent_owner: bool = False
    transaction_type: str = ""  # P-Purchase, S-Sale
    transaction_code: str = ""
    shares: int = 0
    price: float = 0.0
    value: float = 0.0
    ownership_after: int = 0
    transaction_date: datetime | None = None
    filing_date: datetime | None = None
    accession_number: str = ""


@dataclass
class ParsedFiling:
    accession_number: str = ""
    issuer_name: str = ""
    issuer_ticker: str = ""
    issuer_cik: str = ""
    filing_date: datetime | None = None
    transactions: list[ParsedTransaction] = field(default_factory=list)


def parse_form4_xml(xml_content: str, accession_number: str = "") -> ParsedFiling:
    """Parse a Form 4 XML filing and extract transaction data."""
    soup = BeautifulSoup(xml_content, "lxml-xml")
    filing = ParsedFiling(accession_number=accession_number)

    # Parse issuer info
    issuer = soup.find("issuer")
    if issuer:
        filing.issuer_cik = _text(issuer, "issuerCik")
        filing.issuer_name = _text(issuer, "issuerName")
        filing.issuer_ticker = _text(issuer, "issuerTradingSymbol").upper()

    # Parse reporting owner info
    owner = soup.find("reportingOwner")
    insider_name = ""
    insider_cik = ""
    insider_title = ""
    is_director = False
    is_officer = False
    is_ten_pct = False

    if owner:
        owner_id = owner.find("reportingOwnerId")
        if owner_id:
            insider_cik = _text(owner_id, "rptOwnerCik")
            insider_name = _text(owner_id, "rptOwnerName")

        relationship = owner.find("reportingOwnerRelationship")
        if relationship:
            is_director = _text(relationship, "isDirector") == "1"
            is_officer = _text(relationship, "isOfficer") == "1"
            is_ten_pct = _text(relationship, "isTenPercentOwner") == "1"
            insider_title = _text(relationship, "officerTitle")
            if not insider_title:
                if is_director:
                    insider_title = "Director"
                elif is_ten_pct:
                    insider_title = "10% Owner"

    # Parse period of report (filing date)
    period_of_report = _text(soup, "periodOfReport")
    if period_of_report:
        try:
            filing.filing_date = datetime.strptime(period_of_report, "%Y-%m-%d")
        except ValueError:
            pass

    # Parse non-derivative transactions
    for txn_elem in soup.find_all("nonDerivativeTransaction"):
        txn = _parse_transaction(txn_elem, filing, insider_name, insider_cik, insider_title,
                                  is_director, is_officer, is_ten_pct)
        if txn:
            filing.transactions.append(txn)

    # Parse derivative transactions
    for txn_elem in soup.find_all("derivativeTransaction"):
        txn = _parse_transaction(txn_elem, filing, insider_name, insider_cik, insider_title,
                                  is_director, is_officer, is_ten_pct)
        if txn:
            filing.transactions.append(txn)

    return filing


def _parse_transaction(
    txn_elem,
    filing: ParsedFiling,
    insider_name: str,
    insider_cik: str,
    insider_title: str,
    is_director: bool,
    is_officer: bool,
    is_ten_pct: bool,
) -> ParsedTransaction | None:
    """Parse a single transaction element."""
    txn = ParsedTransaction(
        issuer_name=filing.issuer_name,
        issuer_ticker=filing.issuer_ticker,
        issuer_cik=filing.issuer_cik,
        insider_name=insider_name,
        insider_cik=insider_cik,
        insider_title=insider_title,
        is_director=is_director,
        is_officer=is_officer,
        is_ten_percent_owner=is_ten_pct,
        accession_number=filing.accession_number,
        filing_date=filing.filing_date,
    )

    # Transaction date
    date_str = _text(txn_elem, "transactionDate value")
    if not date_str:
        date_str = _text(txn_elem, "transactionDate")
    if date_str:
        try:
            txn.transaction_date = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        except ValueError:
            pass

    # Transaction code (P=Purchase, S=Sale, A=Grant, etc.)
    coding = txn_elem.find("transactionCoding")
    if coding:
        txn.transaction_code = _text(coding, "transactionCode")

    # Map code to type
    if txn.transaction_code in ("P",):
        txn.transaction_type = "P"
    elif txn.transaction_code in ("S",):
        txn.transaction_type = "S"
    else:
        # Skip non-purchase/sale transactions (grants, exercises, etc.)
        return None

    # Shares
    amounts = txn_elem.find("transactionAmounts")
    if amounts:
        shares_str = _text(amounts, "transactionShares value")
        if not shares_str:
            shares_str = _text(amounts, "transactionShares")
        try:
            txn.shares = int(float(shares_str))
        except (ValueError, TypeError):
            pass

        price_str = _text(amounts, "transactionPricePerShare value")
        if not price_str:
            price_str = _text(amounts, "transactionPricePerShare")
        try:
            txn.price = float(price_str)
        except (ValueError, TypeError):
            pass

    txn.value = txn.shares * txn.price

    # Post-transaction holdings
    post_amounts = txn_elem.find("postTransactionAmounts")
    if post_amounts:
        holdings_str = _text(post_amounts, "sharesOwnedFollowingTransaction value")
        if not holdings_str:
            holdings_str = _text(post_amounts, "sharesOwnedFollowingTransaction")
        try:
            txn.ownership_after = int(float(holdings_str))
        except (ValueError, TypeError):
            pass

    return txn


def _text(element, tag: str) -> str:
    """Safely extract text from a BeautifulSoup element."""
    if element is None:
        return ""
    found = element.find(tag)
    if found is None:
        # Try nested tag navigation (e.g., "transactionDate value")
        parts = tag.split()
        current = element
        for part in parts:
            current = current.find(part) if current else None
        if current and current.string:
            return current.string.strip()
        return ""
    return (found.string or "").strip()


def extract_accession_from_url(url: str) -> str:
    """Extract accession number from a filing URL."""
    match = re.search(r"(\d{10}-\d{2}-\d{6})", url)
    if match:
        return match.group(1)
    return ""
