import pytest

from src.data import download


def test_download_graph_retries_transient_overpass_error(monkeypatch):
    calls = 0
    delays = []

    def graph_from_bbox(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls < 3:
            raise download.ResponseStatusCodeError(
                "'overpass-api.de' responded: 502 Bad Gateway"
            )
        return "graph"

    monkeypatch.setattr(download.ox, "graph_from_bbox", graph_from_bbox)
    monkeypatch.setattr(download.time, "sleep", delays.append)

    result = download._download_graph(
        (1, 2, 3, 4),
        {
            "network_type": "drive",
            "custom_filter": None,
        },
        {
            "simplify": True,
            "retain_all": False,
            "overpass_retries": 2,
            "overpass_backoff_seconds": 1,
        },
    )

    assert result == "graph"
    assert calls == 3
    assert delays == [1, 2]


def test_download_graph_does_not_retry_non_transient_overpass_error(monkeypatch):
    calls = 0

    def graph_from_bbox(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise download.ResponseStatusCodeError(
            "'overpass-api.de' responded: 400 Bad Request"
        )

    monkeypatch.setattr(download.ox, "graph_from_bbox", graph_from_bbox)
    monkeypatch.setattr(download.time, "sleep", lambda seconds: pytest.fail("slept"))

    with pytest.raises(download.ResponseStatusCodeError):
        download._download_graph(
            (1, 2, 3, 4),
            {"network_type": "drive", "custom_filter": None},
            {
                "simplify": True,
                "retain_all": False,
                "overpass_retries": 2,
                "overpass_backoff_seconds": 1,
            },
        )

    assert calls == 1
