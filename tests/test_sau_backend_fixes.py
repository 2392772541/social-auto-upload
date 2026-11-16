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


def test_publish_history_record_and_delete(tmp_path, monkeypatch):
    monkeypatch.setattr(sau_backend, "BASE_DIR", tmp_path)
    sau_backend.ensure_runtime_ready()
    client = sau_backend.app.test_client()

    with patch.object(sau_backend, "post_video_DouYin", return_value=None):
        resp = client.post(
            "/postVideo",
            json={
                "type": 3,
                "title": "测试历史记录标题",
                "tags": ["效率", "工具"],
                "fileList": ["demo.mp4"],
                "accountList": ["acc.json"],
                "enableTimer": 1,
                "videosPerDay": 1,
                "dailyTimes": ["10:00"],
                "startDays": 0,
            },
        )
    assert resp.status_code == 200

    hist_resp = client.get("/getPublishHistory")
    assert hist_resp.status_code == 200
    rows = hist_resp.get_json()["data"]
    assert len(rows) == 1
    assert rows[0]["title"] == "测试历史记录标题"
    assert rows[0]["platform_name"] == "抖音"
    assert rows[0]["status"] == "success"

    del_resp = client.get(f"/deletePublishRecord?id={rows[0]['id']}")
    assert del_resp.status_code == 200
    assert client.get("/getPublishHistory").get_json()["data"] == []


def test_title_template_crud(tmp_path, monkeypatch):
    monkeypatch.setattr(sau_backend, "BASE_DIR", tmp_path)
    sau_backend.ensure_runtime_ready()
    client = sau_backend.app.test_client()

    # 默认有预置模板
    list_resp = client.get("/getTitleTemplates")
    assert list_resp.status_code == 200
    initial = list_resp.get_json()["data"]
    assert len(initial) >= 4

    # 新增标题模板
    create_resp = client.post(
        "/saveTitleTemplate",
        json={
            "category": "科技",
            "title": "AI效率神器实测分享",
            "tags": ["AI工具", "效率"],
            "note": "通用科技类开场",
        },
    )
    assert create_resp.status_code == 200
    new_id = create_resp.get_json()["data"]["id"]

    # 搜索筛选
    filtered = client.get("/getTitleTemplates?category=科技&keyword=AI").get_json()["data"]
    assert len(filtered) == 1
    assert filtered[0]["id"] == new_id
    assert filtered[0]["tags"] == ["AI工具", "效率"]

    # 更新
    upd_resp = client.post(
        "/saveTitleTemplate",
        json={"id": new_id, "category": "科技", "title": "更新后的AI标题", "tags": "AI, 职场"},
    )
    assert upd_resp.status_code == 200
    updated = client.get("/getTitleTemplates?category=科技").get_json()["data"]
    assert updated[0]["title"] == "更新后的AI标题"
    assert updated[0]["tags"] == ["AI", "职场"]

    # 删除
    assert client.get(f"/deleteTitleTemplate?id={new_id}").status_code == 200
    assert client.get("/getTitleTemplates?category=科技").get_json()["data"] == []
