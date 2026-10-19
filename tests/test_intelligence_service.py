import sys
from pathlib import Path
from types import ModuleType
from types import SimpleNamespace
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


class FakeBlueprint:
    def __init__(self, *args, **kwargs):
        pass

    def route(self, *args, **kwargs):
        return lambda handler: handler


flask_module = ModuleType("flask")
flask_module.Blueprint = FakeBlueprint
flask_module.request = SimpleNamespace()
flask_module.jsonify = lambda payload: payload
sys.modules["flask"] = flask_module

from src.routes import query_routes


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


@pytest.mark.parametrize("payload", [None, [], {"longitude": 151.2}])
def test_invalid_query_payload_returns_bad_request(monkeypatch, payload):
    monkeypatch.setattr(query_routes.request, "get_json", lambda silent: payload, raising=False)

    response, status_code = query_routes.query_intelligence()

    assert status_code == 400
    assert response["status"] == "error"


def test_query_preserves_zero_valued_optional_parameters(monkeypatch):
    payload = {
        "latitude": 0,
        "longitude": 0,
        "destination_lat": 0,
        "destination_lon": 0,
        "hour_of_day": 0,
    }
    monkeypatch.setattr(query_routes.request, "get_json", lambda silent: payload, raising=False)
    monkeypatch.setattr(query_routes, "get_consumer_intelligence", lambda **kwargs: kwargs)

    response = query_routes.query_intelligence()

    assert response["lat"] == 0
    assert response["lon"] == 0
    assert response["destination_lat"] == 0
    assert response["destination_lon"] == 0
    assert response["hour_of_day"] == 0