import logging
import re
from datetime import datetime

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.etl.parser import ParsedFiling, parse_form4_xml
from app.etl.sec_client import sec_client
from app.models.models import Alert, Company, Insider, Transaction

logger = logging.getLogger(__name__)


def ingest_recent_filings():
    """Main ingestion entry point: fetch and process recent Form 4 filings."""
    logger.info("Starting Form 4 ingestion...")
    db = SessionLocal()
    try:
        filings = _fetch_recent_form4_urls()
        processed = 0
        for accession_number, filing_url in filings:
            if _filing_exists(db, accession_number):
                continue
            try:
                xml_content = sec_client.get_filing_document(filing_url)
                parsed = parse_form4_xml(xml_content, accession_number)
                if parsed.transactions:
                    _store_filing(db, parsed)
                    processed += 1
            except Exception:
                logger.exception("Error processing filing %s", accession_number)
                continue
        logger.info("Ingestion complete. Processed %d new filings.", processed)

        # Run alert detection after ingestion
        detect_unusual_activity(db)
        db.commit()
    except Exception:
        logger.exception("Ingestion failed")
        db.rollback()
    finally:
        db.close()


def _fetch_recent_form4_urls() -> list[tuple[str, str]]:
    """Fetch recent Form 4 filing URLs from SEC EDGAR RSS feed."""
    filings = []
    try:
        rss_content = sec_client.get_recent_filings_rss()
        soup = BeautifulSoup(rss_content, "lxml-xml")
        entries = soup.find_all("entry")
        for entry in entries:
            link = entry.find("link")
            if link and link.get("href"):
                index_url = link["href"]
                accession = _extract_accession(index_url)
                if accession:
                    # Convert index page URL to XML document URL
                    xml_url = _resolve_xml_url(index_url)
                    if xml_url:
                        filings.append((accession, xml_url))
    except Exception:
        logger.exception("Error fetching RSS feed")
    logger.info("Found %d Form 4 filing URLs", len(filings))
    return filings


def _resolve_xml_url(index_url: str) -> str | None:
    """Given a filing index page URL, find the primary XML document URL."""
    try:
        html = sec_client.get_filing_document(index_url)
        soup = BeautifulSoup(html, "html.parser")
        # Look for the primary XML document link in the filing index
        for a_tag in soup.find_all("a"):
            href = a_tag.get("href", "")
            if href.endswith(".xml") and "primary_doc" not in href:
                if not href.startswith("http"):
                    href = f"https://www.sec.gov{href}"
                return href
        # Fallback: try to find any XML link
        for a_tag in soup.find_all("a"):
            href = a_tag.get("href", "")
            if ".xml" in href:
                if not href.startswith("http"):
                    href = f"https://www.sec.gov{href}"
                return href
    except Exception:
        logger.exception("Error resolving XML URL for %s", index_url)
    return None


def _extract_accession(url: str) -> str:
    """Extract accession number from URL."""
    match = re.search(r"(\d{10}-\d{2}-\d{6})", url)
    return match.group(1) if match else ""


def _filing_exists(db: Session, accession_number: str) -> bool:
    """Check if a filing has already been processed."""
    return (
        db.query(Transaction)
        .filter(Transaction.accession_number == accession_number)
        .first()
        is not None
    )


def _store_filing(db: Session, filing: ParsedFiling):
    """Store parsed filing data in the database."""
    # Get or create company
    company = _get_or_create_company(db, filing)

    for txn_data in filing.transactions:
        # Get or create insider
        insider = _get_or_create_insider(db, txn_data, company)

        # Create transaction
        transaction = Transaction(
            company_id=company.id,
            insider_id=insider.id,
            transaction_type=txn_data.transaction_type,
            shares=txn_data.shares,
            price=txn_data.price,
            value=txn_data.value,
            ownership_after=txn_data.ownership_after,
            transaction_date=txn_data.transaction_date or datetime.now(),
            filing_date=txn_data.filing_date or datetime.now(),
            form_type="4",
            accession_number=txn_data.accession_number,
        )

        # Calculate ownership change percentage
        if txn_data.ownership_after and txn_data.shares:
            previous_ownership = txn_data.ownership_after + txn_data.shares
            if previous_ownership > 0:
                transaction.ownership_change_pct = (
                    txn_data.shares / previous_ownership
                ) * 100

        db.add(transaction)

    db.commit()
    logger.info(
        "Stored %d transactions for %s (%s)",
        len(filing.transactions),
        filing.issuer_name,
        filing.issuer_ticker,
    )


def _get_or_create_company(db: Session, filing: ParsedFiling) -> Company:
    """Get existing company or create new one."""
    company = db.query(Company).filter(Company.cik == filing.issuer_cik).first()
    if not company:
        company = Company(
            ticker=filing.issuer_ticker,
            name=filing.issuer_name,
            cik=filing.issuer_cik,
        )
        db.add(company)
        db.flush()
    return company


def _get_or_create_insider(db: Session, txn_data, company: Company) -> Insider:
    """Get existing insider or create new one."""
    insider = (
        db.query(Insider)
        .filter(Insider.company_id == company.id, Insider.name == txn_data.insider_name)
        .first()
    )
    if not insider:
        insider = Insider(
            name=txn_data.insider_name,
            title=txn_data.insider_title,
            company_id=company.id,
            cik=txn_data.insider_cik,
        )
        db.add(insider)
        db.flush()
    return insider


def detect_unusual_activity(db: Session):
    """Detect unusual insider activity and create alerts."""
    _detect_cluster_selling(db)
    _detect_large_sales(db)
    _detect_ownership_reduction(db)


def _detect_cluster_selling(db: Session):
    """Flag when >= 3 insiders sell within 7 days for the same company."""
    from sqlalchemy import func, text

    query = text("""
        SELECT company_id, COUNT(DISTINCT insider_id) as seller_count,
               SUM(value) as total_value
        FROM transactions
        WHERE transaction_type = 'S'
          AND transaction_date >= NOW() - INTERVAL '7 days'
        GROUP BY company_id
        HAVING COUNT(DISTINCT insider_id) >= 3
    """)
    results = db.execute(query).fetchall()
    for row in results:
        company_id, seller_count, total_value = row
        existing = (
            db.query(Alert)
            .filter(
                Alert.company_id == company_id,
                Alert.alert_type == "cluster_selling",
                Alert.created_at >= func.now() - text("INTERVAL '1 day'"),
            )
            .first()
        )
        if not existing:
            alert = Alert(
                company_id=company_id,
                alert_type="cluster_selling",
                description=f"{seller_count} insiders sold within 7 days, total value ${total_value:,.0f}",
                severity="high",
            )
            db.add(alert)


def _detect_large_sales(db: Session):
    """Flag sales over $5M."""
    from sqlalchemy import func, text

    recent_large = (
        db.query(Transaction)
        .filter(
            Transaction.transaction_type == "S",
            Transaction.value > 5_000_000,
            Transaction.created_at >= func.now() - text("INTERVAL '1 day'"),
        )
        .all()
    )
    for txn in recent_large:
        existing = (
            db.query(Alert)
            .filter(
                Alert.company_id == txn.company_id,
                Alert.alert_type == "large_sale",
                Alert.transaction_ids.contains(str(txn.id)),
            )
            .first()
        )
        if not existing:
            alert = Alert(
                company_id=txn.company_id,
                alert_type="large_sale",
                description=f"Large insider sale: ${txn.value:,.0f}",
                severity="high",
                transaction_ids=str(txn.id),
            )
            db.add(alert)


def _detect_ownership_reduction(db: Session):
    """Flag when ownership drops by more than 10%."""
    from sqlalchemy import func, text

    recent = (
        db.query(Transaction)
        .filter(
            Transaction.transaction_type == "S",
            Transaction.ownership_change_pct is not None,
            Transaction.ownership_change_pct > 10,
            Transaction.created_at >= func.now() - text("INTERVAL '1 day'"),
        )
        .all()
    )
    for txn in recent:
        existing = (
            db.query(Alert)
            .filter(
                Alert.company_id == txn.company_id,
                Alert.alert_type == "ownership_reduction",
                Alert.transaction_ids.contains(str(txn.id)),
            )
            .first()
        )
        if not existing:
            alert = Alert(
                company_id=txn.company_id,
                alert_type="ownership_reduction",
                description=f"Insider reduced ownership by {txn.ownership_change_pct:.1f}%",
                severity="medium",
                transaction_ids=str(txn.id),
            )
            db.add(alert)
