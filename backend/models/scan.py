"""Scan ORM model."""
from extensions import db
from utils.helpers import utcnow


class Scan(db.Model):
    __tablename__ = "scans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    url = db.Column(db.String(2048), nullable=False)
    domain = db.Column(db.String(255), nullable=False, index=True)
    report = db.Column(db.Text, nullable=False)  # JSON
    score = db.Column(db.Integer, index=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    scan_duration_ms = db.Column(db.Integer)

    __table_args__ = (
        db.Index("idx_scan_user_created", "user_id", "created_at"),
        db.Index("idx_scan_domain_created", "domain", "created_at"),
    )
