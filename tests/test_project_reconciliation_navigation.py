from app.guided_workflow_ui import _STAGE_ROUTES
from app.turing_generator_navigation import (
    APP_VIEW_RECONCILIATION,
    APP_VIEWS,
)


def test_project_reconciliation_is_stable_top_level_view():
    assert APP_VIEW_RECONCILIATION == "project_reconciliation"
    assert APP_VIEW_RECONCILIATION in APP_VIEWS


def test_guided_project_reconciliation_stage_routes_to_dedicated_view():
    route = _STAGE_ROUTES["project_reconciliation"]
    assert route[0] == APP_VIEW_RECONCILIATION
