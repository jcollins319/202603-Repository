from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.models import Alert
from app.models.schemas import AlertResponse

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("/", response_model=list[AlertResponse])
def get_alerts(
    alert_type: str | None = None,
    severity: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Get alerts with optional filtering."""
    query = db.query(Alert).options(joinedload(Alert.company))

    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    if severity:
        query = query.filter(Alert.severity == severity)

    results = (
        query.order_by(desc(Alert.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return results
