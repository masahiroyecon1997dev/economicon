"""selection_models テスト共通フィクスチャ"""

import pytest
from fastapi.testclient import TestClient

from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.tables_store import TablesStore
from main import app


@pytest.fixture
def client():
    """TestClient のフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_store():
    """TablesStore のフィクスチャ"""
    store = TablesStore()
    store.clear_tables()

    result_store = AnalysisResultStore()
    result_store.clear_all()

    yield store

    store.clear_tables()
    result_store.clear_all()
