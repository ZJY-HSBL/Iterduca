from iterduca.services.connection_view import (
    connection_id,
    non_negative_int,
    summarize_connections,
)


def test_connection_summary_ignores_invalid_rows_and_clamps_bytes() -> None:
    summary = summarize_connections(
        [
            {"id": "a", "upload": 100, "download": 200},
            {"id": "b", "upload": "50", "download": -10},
            None,
            "bad",
        ]
    )

    assert summary.count == 2
    assert summary.upload == 150
    assert summary.download == 200


def test_connection_id_and_number_helpers_are_defensive() -> None:
    assert connection_id({"id": "abc"}) == "abc"
    assert connection_id({"id": ""}) == ""
    assert connection_id(None) == ""
    assert non_negative_int("42") == 42
    assert non_negative_int("-1") == 0
    assert non_negative_int("bad") == 0
