from app.api.ws.interview import router


def test_voice_websocket_route_is_defined() -> None:
    ws_paths = [route.path for route in router.routes if hasattr(route, "path")]

    assert ws_paths == ["/ws/interview/{session_id}"]
