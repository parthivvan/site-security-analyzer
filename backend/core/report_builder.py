"""
BACKWARDS COMPATIBILITY SHIM.

The canonical implementation now lives in services.scorer.
This file re-exports everything so existing imports continue to work.
"""
from services.scorer import (          # noqa: F401
    build_flat_report,
    compute_score_from_flat_report,
    enrich_scan_result,
    build_priority_actions,
    build_risk_snapshot,
    build_explanation,
    grade_for_score,
    LABELS,
    CHECK_WEIGHTS,
    REMEDIATION_LIBRARY,
)
