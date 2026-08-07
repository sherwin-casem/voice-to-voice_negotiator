import uuid
from unittest.mock import patch

import pytest
from fastapi import WebSocketException

from app.config import Settings
from app.modules.auth.service import create_ws_ticket
from app.modules.auth.ws import parse_ws_user_id


def test_valid_ticket_authenticates() -> None:
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    ticket = create_ws_ticket(user_id, session_id)

    assert parse_ws_user_id(session_id, ticket=ticket, user_id=None) == user_id


def test_ticket_bound_to_other_session_rejected() -> None:
    user_id = uuid.uuid4()
    ticket = create_ws_ticket(user_id, uuid.uuid4())

    with pytest.raises(WebSocketException, match="does not match"):
        parse_ws_user_id(uuid.uuid4(), ticket=ticket, user_id=None)


def test_garbage_ticket_rejected() -> None:
    with pytest.raises(WebSocketException):
        parse_ws_user_id(uuid.uuid4(), ticket="not-a-ticket", user_id=None)


def test_bare_user_id_rejected_in_production() -> None:
    production = Settings(app_env="production", allow_dev_user_header=False)

    with patch("app.modules.auth.ws.settings", production):
        with pytest.raises(WebSocketException, match="Authentication required"):
            parse_ws_user_id(uuid.uuid4(), ticket=None, user_id=str(uuid.uuid4()))


def test_bare_user_id_rejected_even_with_dev_header_flag_in_production() -> None:
    """ALLOW_DEV_USER_HEADER must not bypass auth outside development."""
    misconfigured = Settings(app_env="production", allow_dev_user_header=True)

    with patch("app.modules.auth.ws.settings", misconfigured):
        with pytest.raises(WebSocketException, match="Authentication required"):
            parse_ws_user_id(uuid.uuid4(), ticket=None, user_id=str(uuid.uuid4()))


def test_bare_user_id_allowed_in_development() -> None:
    development = Settings(app_env="development", allow_dev_user_header=True)
    user_id = uuid.uuid4()

    with patch("app.modules.auth.ws.settings", development):
        assert parse_ws_user_id(uuid.uuid4(), ticket=None, user_id=str(user_id)) == user_id


def test_missing_credentials_rejected() -> None:
    with pytest.raises(WebSocketException, match="Authentication required"):
        parse_ws_user_id(uuid.uuid4(), ticket=None, user_id=None)
