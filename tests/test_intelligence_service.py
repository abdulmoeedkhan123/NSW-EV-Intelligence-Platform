import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import pytest


APP_ROOT = Path(__file__).resolve().parents[1] / "nsw-ev-intelligence"
sys.path.insert(0, str(APP_ROOT))

if "databricks" not in sys.modules:
    databricks_module = ModuleType("databricks")
    databricks_sql_module = ModuleType("databricks.sql")
    databricks_module.sql = databricks_sql_module
    sys.modules["databricks"] = databricks_module
    sys.modules["databricks.sql"] = databricks_sql_module

from src.services import intelligence_service


class FakeCursor:
    def __init__(self):
        self.query = None
        self.parameters = None

    def execute(self, query, parameters):
        self.query = query
        self.parameters = parameters

    def fetchall(self):
        return []

    def close(self):
        pass


class FakeConnection:
    def __init__(self):
        self.fake_cursor = FakeCursor()

    def cursor(self):
        return self.fake_cursor


def test_charger_type_is_bound_as_sql_parameter():
    connection = FakeConnection()
    malicious_filter = "' OR 1=1 --"

    with patch.object(intelligence_service, "get_sql_connection", return_value=connection):
        result = intelligence_service.get_consumer_intelligence(
            lat=-33.86,
            lon=151.20,
            charger_type=malicious_filter,
        )

    assert result["status"] == "success"
    assert "charger__type = ?" in connection.fake_cursor.query
    assert malicious_filter not in connection.fake_cursor.query
    assert connection.fake_cursor.parameters == [-33.86, -33.86, 151.20, 30.0, malicious_filter]