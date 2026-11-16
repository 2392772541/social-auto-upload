import asyncio
import io
from datetime import datetime
from pathlib import Path
from queue import Queue
from unittest.mock import patch

import sau_backend
from myUtils import auth as my_auth
from myUtils import postVideo


def test_runtime_ready_creates_dirs_and_tables(tmp_path, monkeypatch):
    monkeypatch.setattr(sau_backend, "BASE_DIR", tmp_path)
    sau_backend.ensure_runtime_ready()
    assert (tmp_path / "videoFile").is_dir()
    assert (tmp_path / "cookiesFile").is_dir()
    assert (tmp_path / "db" / "database.db").is_file()

    client = sau_backend.app.test_client()
    resp = client.get("/getAccounts")
    assert resp.status_code == 200
    assert resp.get_json()["code"] == 200
    assert resp.get_json()["data"] == []


def test_get_file_blocks_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(sau_backend, "BASE_DIR", tmp_path)
    sau_backend.ensure_runtime_ready()
    client = sau_backend.app.test_client()

    for bad_name in ("../conf.py", "..\\conf.py", "C:/Windows/win.ini", "."):
        resp = client.get("/getFile", query_string={"filename": bad_name})
        assert resp.status_code == 400


def test_upload_sanitizes_filename(tmp_path, monkeypatch):
    monkeypatch.setattr(sau_backend, "BASE_DIR", tmp_path)
    sau_backend.ensure_runtime_ready()
    client = sau_backend.app.test_client()

    resp = client.post(
        "/upload",
        data={"file": (io.BytesIO(b"dummy-video"), "../../evil.mp4")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    saved_name = resp.get_json()["data"]
    assert "/" not in saved_name and "\\" not in saved_name and ".." not in saved_name
    assert saved_name.endswith("_evil.mp4")
    assert (tmp_path / "videoFile" / saved_name).is_file()


def test_login_validation_and_sse_error_exit():
    client = sau_backend.app.test_client()
    assert client.get("/login?type=9&id=test").status_code == 400
    assert client.get("/login?type=3&id=").status_code == 400

    q = Queue()
    sau_backend.active_queues["test-key"] = q
    with patch.object(sau_backend, "douyin_cookie_gen", side_effect=RuntimeError("boom")):
        sau_backend.run_async_function("3", "user1", q)

    chunks = list(sau_backend.sse_stream(q, queue_key="test-key", timeout_seconds=5))
    assert chunks == ["data: 500\n\n"]
    assert "test-key" not in sau_backend.active_queues


def test_check_cookie_missing_file_returns_false(tmp_path, monkeypatch):
    monkeypatch.setattr(my_auth, "BASE_DIR", tmp_path)
    (tmp_path / "cookiesFile").mkdir(parents=True, exist_ok=True)
    assert asyncio.run(my_auth.check_cookie(3, "nonexistent.json")) is False


def test_post_video_scheduled_passes_single_datetime_and_strategy(tmp_path, monkeypatch):
    monkeypatch.setattr(postVideo, "BASE_DIR", tmp_path)
    captured = {}

    class DummyUploader:
        def __init__(self, *args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs

        async def main(self):
            return None

        async def douyin_upload_video(self):
            return None

    monkeypatch.setattr(postVideo, "XiaoHongShuVideo", DummyUploader)
    postVideo.post_video_xhs(
        "测试标题",
        ["a.mp4"],
        ["tag1"],
        ["cookie.json"],
        enableTimer=True,
        videos_per_day=1,
        daily_times=["10:00"],
        start_days=1,
    )
    assert isinstance(captured["args"][3], datetime)
    assert captured["kwargs"]["publish_strategy"] == "scheduled"

    captured.clear()
    monkeypatch.setattr(postVideo, "DouYinVideo", DummyUploader)
    postVideo.post_video_DouYin(
        "测试抖音",
        ["a.mp4"],
        ["tag1"],
        ["cookie.json"],
        enableTimer=True,
        videos_per_day=1,
        daily_times=["10:00"],
        start_days=1,
    )
    assert isinstance(captured["args"][3], datetime)
    assert captured["kwargs"]["publish_strategy"] == "scheduled"

    captured.clear()
    monkeypatch.setattr(postVideo, "KSVideo", DummyUploader)
    postVideo.post_video_ks(
        "测试快手",
        ["a.mp4"],
        ["tag1"],
        ["cookie.json"],
        enableTimer=True,
        videos_per_day=1,
        daily_times=["10:00"],
        start_days=1,
    )
    assert isinstance(captured["args"][3], datetime)
    assert captured["kwargs"]["publish_strategy"] == "scheduled"
