import asyncio
import json
import os
import sqlite3
import threading
import time
import uuid
from queue import Empty, Queue
from pathlib import Path
from flask_cors import CORS
from myUtils.auth import check_cookie
from flask import Flask, request, jsonify, Response, render_template, send_from_directory
from conf import BASE_DIR
from myUtils.login import get_tencent_cookie, douyin_cookie_gen, get_ks_cookie, xiaohongshu_cookie_gen
from myUtils.postVideo import post_video_tencent, post_video_DouYin, post_video_ks, post_video_xhs

active_queues = {}
active_queues_lock = threading.Lock()
app = Flask(__name__)


def ensure_runtime_ready():
    """Ensure required directories and SQLite tables exist before handling requests."""
    for subdir in ("videoFile", "cookiesFile", "db"):
        Path(BASE_DIR / subdir).mkdir(parents=True, exist_ok=True)

    db_path = Path(BASE_DIR / "db" / "database.db")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type INTEGER NOT NULL,
            filePath TEXT NOT NULL,
            userName TEXT NOT NULL,
            status INTEGER DEFAULT 0
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filesize REAL,
            upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS publish_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform_type INTEGER NOT NULL,
            title TEXT NOT NULL,
            file_list TEXT NOT NULL,
            account_list TEXT NOT NULL,
            tags TEXT,
            enable_timer INTEGER DEFAULT 0,
            schedule_summary TEXT,
            is_draft INTEGER DEFAULT 0,
            status TEXT NOT NULL,
            message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS title_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT DEFAULT '通用',
            title TEXT NOT NULL,
            tags TEXT,
            note TEXT DEFAULT '',
            use_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        existing_tpl_count = cursor.execute("SELECT COUNT(1) FROM title_templates").fetchone()[0]
        if existing_tpl_count == 0:
            seed_templates = [
                ("干货拆解", "【干货必看】3分钟讲清楚核心逻辑，建议先收藏再慢慢看！", ["干货分享", "效率提升"], "适合知识科普、方法总结类视频"),
                ("好物测评", "真实体验一周后才敢说实话：到底值不值得入手？", ["好物推荐", "真实测评"], "适合产品开箱、工具对比视频"),
                ("教程实操", "保姆级手把手教学，跟着做一遍就能学会！", ["教程", "新手必看"], "适合分步教学、软件演示视频"),
                ("日常Vlog", "记录生活里的小确幸，今天也请继续加油呀！", ["日常", "Vlog"], "适合生活碎片、日常记录"),
            ]
            for cat, ttl, tgs, nt in seed_templates:
                cursor.execute(
                    "INSERT INTO title_templates (category, title, tags, note) VALUES (?, ?, ?, ?)",
                    (cat, ttl, json.dumps(tgs, ensure_ascii=False), nt),
                )
        conn.commit()


ensure_runtime_ready()


def record_publish_history(
    platform_type,
    title,
    file_list,
    account_list,
    tags,
    enable_timer,
    videos_per_day,
    daily_times,
    start_days,
    is_draft,
    status,
    message='',
):
    """Persist publish execution summary so users can inspect & reuse history."""
    ensure_runtime_ready()
    schedule_summary = ''
    if enable_timer:
        times_text = ', '.join(str(t) for t in (daily_times or []))
        start_label = '明天' if start_days == 0 else ('后天' if start_days == 1 else f'{start_days}天后')
        schedule_summary = f'定时({start_label}起，每天{videos_per_day or 1}条 {times_text})'
    else:
        schedule_summary = '立即发布'

    db_path = Path(BASE_DIR / "db" / "database.db")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO publish_records (
                platform_type, title, file_list, account_list, tags,
                enable_timer, schedule_summary, is_draft, status, message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                int(platform_type or 0),
                str(title or ''),
                json.dumps(file_list or [], ensure_ascii=False),
                json.dumps(account_list or [], ensure_ascii=False),
                json.dumps(tags or [], ensure_ascii=False),
                1 if enable_timer else 0,
                schedule_summary,
                1 if is_draft else 0,
                status,
                str(message or ''),
            ),
        )
        conn.commit()

#允许所有来源跨域访问
CORS(app)

# 限制上传文件大小为160MB
app.config['MAX_CONTENT_LENGTH'] = 160 * 1024 * 1024

# 获取当前目录（假设 index.html 和 assets 在这里）
current_dir = os.path.dirname(os.path.abspath(__file__))

# 处理所有静态资源请求（未来打包用）
@app.route('/assets/<filename>')
def custom_static(filename):
    return send_from_directory(os.path.join(current_dir, 'assets'), filename)

# 处理 favicon.ico 静态资源（未来打包用）
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_dir, 'assets'), 'vite.svg')

@app.route('/vite.svg')
def vite_svg():
    return send_from_directory(os.path.join(current_dir, 'assets'), 'vite.svg')

# （未来打包用）
@app.route('/')
def index():  # put application's code here
    return send_from_directory(current_dir, 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No file part in the request"
        }), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No selected file"
        }), 400
    try:
        # 保存文件到指定位置
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        safe_name = Path(file.filename).name
        if not safe_name:
            return jsonify({"code": 400, "data": None, "msg": "Invalid filename"}), 400
        video_dir = Path(BASE_DIR / "videoFile")
        video_dir.mkdir(parents=True, exist_ok=True)
        saved_name = f"{uuid_v1}_{safe_name}"
        filepath = video_dir / saved_name
        file.save(filepath)
        return jsonify({"code":200,"msg": "File uploaded successfully", "data": saved_name}), 200
    except Exception as e:
        return jsonify({"code":500,"msg": str(e),"data":None}), 500

@app.route('/getFile', methods=['GET'])
def get_file():
    # 获取 filename 参数
    filename = request.args.get('filename')

    if not filename:
        return jsonify({"code": 400, "msg": "filename is required", "data": None}), 400

    # 防止路径穿越攻击
    base_dir = Path(BASE_DIR / "videoFile").resolve()
    target_path = (base_dir / filename).resolve()
    if not target_path.is_relative_to(base_dir) or target_path == base_dir:
        return jsonify({"code": 400, "msg": "Invalid filename", "data": None}), 400

    # 拼接完整路径
    file_path = str(base_dir)

    # 返回文件
    return send_from_directory(file_path, target_path.name)


@app.route('/uploadSave', methods=['POST'])
def upload_save():
    if 'file' not in request.files:
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No file part in the request"
        }), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No selected file"
        }), 400

    # 获取表单中的自定义文件名（可选）
    custom_filename = request.form.get('filename', None)
    original_name = Path(file.filename).name
    if not original_name:
        return jsonify({"code": 400, "data": None, "msg": "Invalid filename"}), 400
    if custom_filename:
        safe_custom = Path(custom_filename).name
        ext = original_name.rsplit('.', 1)[-1] if '.' in original_name else ''
        filename = f"{safe_custom}.{ext}" if ext else safe_custom
    else:
        filename = original_name

    try:
        # 生成 UUID v1
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")

        # 构造文件名和路径
        final_filename = f"{uuid_v1}_{filename}"
        video_dir = Path(BASE_DIR / "videoFile")
        video_dir.mkdir(parents=True, exist_ok=True)
        filepath = video_dir / final_filename

        # 保存文件
        file.save(filepath)

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                                INSERT INTO file_records (filename, filesize, file_path)
            VALUES (?, ?, ?)
                                ''', (filename, round(float(os.path.getsize(filepath)) / (1024 * 1024),2), final_filename))
            conn.commit()
            print("✅ 上传文件已记录")

        return jsonify({
            "code": 200,
            "msg": "File uploaded and saved successfully",
            "data": {
                "filename": filename,
                "filepath": final_filename
            }
        }), 200

    except Exception as e:
        print(f"Upload failed: {e}")
        return jsonify({
            "code": 500,
            "msg": f"upload failed: {e}",
            "data": None
        }), 500

@app.route('/getFiles', methods=['GET'])
def get_all_files():
    try:
        # 使用 with 自动管理数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row  # 允许通过列名访问结果
            cursor = conn.cursor()

            # 查询所有记录
            cursor.execute("SELECT * FROM file_records")
            rows = cursor.fetchall()

            # 将结果转为字典列表，并提取UUID
            data = []
            for row in rows:
                row_dict = dict(row)
                # 从 file_path 中提取 UUID (文件名的第一部分，下划线前)
                if row_dict.get('file_path'):
                    file_path_parts = row_dict['file_path'].split('_', 1)  # 只分割第一个下划线
                    if len(file_path_parts) > 0:
                        row_dict['uuid'] = file_path_parts[0]  # UUID 部分
                    else:
                        row_dict['uuid'] = ''
                else:
                    row_dict['uuid'] = ''
                data.append(row_dict)

            return jsonify({
                "code": 200,
                "msg": "success",
                "data": data
            }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("get file failed!"),
            "data": None
        }), 500


@app.route("/getAccounts", methods=['GET'])
def getAccounts():
    """快速获取所有账号信息，不进行cookie验证"""
    try:
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
            SELECT * FROM user_info''')
            rows = cursor.fetchall()
            rows_list = [list(row) for row in rows]

            print("\n📋 当前数据表内容（快速获取）：")
            for row in rows:
                print(row)

            return jsonify(
                {
                    "code": 200,
                    "msg": None,
                    "data": rows_list
                }), 200
    except Exception as e:
        print(f"获取账号列表时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"获取账号列表失败: {str(e)}",
            "data": None
        }), 500


@app.route("/getValidAccounts",methods=['GET'])
async def getValidAccounts():
    with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT * FROM user_info''')
        rows = cursor.fetchall()
        rows_list = [list(row) for row in rows]
        print("\n📋 当前数据表内容：")
        for row in rows:
            print(row)
        for row in rows_list:
            try:
                flag = await check_cookie(row[1], row[2])
            except Exception as e:
                print(f"⚠️ 验证账号 {row[3]} Cookie 异常: {e}")
                flag = False
            if not flag:
                row[4] = 0
                cursor.execute('''
                UPDATE user_info 
                SET status = ? 
                WHERE id = ?
                ''', (0,row[0]))
                conn.commit()
                print("✅ 用户状态已更新")
            elif row[4] != 1:
                row[4] = 1
                cursor.execute('''
                UPDATE user_info 
                SET status = ? 
                WHERE id = ?
                ''', (1, row[0]))
                conn.commit()
        for row in rows:
            print(row)
        return jsonify(
                        {
                            "code": 200,
                            "msg": None,
                            "data": rows_list
                        }),200

@app.route('/deleteFile', methods=['GET'])
def delete_file():
    file_id = request.args.get('id')

    if not file_id or not file_id.isdigit():
        return jsonify({
            "code": 400,
            "msg": "Invalid or missing file ID",
            "data": None
        }), 400

    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询要删除的记录
            cursor.execute("SELECT * FROM file_records WHERE id = ?", (file_id,))
            record = cursor.fetchone()

            if not record:
                return jsonify({
                    "code": 404,
                    "msg": "File not found",
                    "data": None
                }), 404

            record = dict(record)

            # 获取文件路径并删除实际文件
            file_path = Path(BASE_DIR / "videoFile" / record['file_path'])
            if file_path.exists():
                try:
                    file_path.unlink()  # 删除文件
                    print(f"✅ 实际文件已删除: {file_path}")
                except Exception as e:
                    print(f"⚠️ 删除实际文件失败: {e}")
                    # 即使删除文件失败，也要继续删除数据库记录，避免数据不一致
            else:
                print(f"⚠️ 实际文件不存在: {file_path}")

            # 删除数据库记录
            cursor.execute("DELETE FROM file_records WHERE id = ?", (file_id,))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "File deleted successfully",
            "data": {
                "id": record['id'],
                "filename": record['filename']
            }
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("delete failed!"),
            "data": None
        }), 500

@app.route('/deleteAccount', methods=['GET'])
def delete_account():
    account_id = request.args.get('id')

    if not account_id or not account_id.isdigit():
        return jsonify({
            "code": 400,
            "msg": "Invalid or missing account ID",
            "data": None
        }), 400

    account_id = int(account_id)

    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询要删除的记录
            cursor.execute("SELECT * FROM user_info WHERE id = ?", (account_id,))
            record = cursor.fetchone()

            if not record:
                return jsonify({
                    "code": 404,
                    "msg": "account not found",
                    "data": None
                }), 404

            record = dict(record)

            # 删除关联的cookie文件
            if record.get('filePath'):
                cookie_file_path = Path(BASE_DIR / "cookiesFile" / record['filePath'])
                if cookie_file_path.exists():
                    try:
                        cookie_file_path.unlink()
                        print(f"✅ Cookie文件已删除: {cookie_file_path}")
                    except Exception as e:
                        print(f"⚠️ 删除Cookie文件失败: {e}")

            # 删除数据库记录
            cursor.execute("DELETE FROM user_info WHERE id = ?", (account_id,))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "account deleted successfully",
            "data": None
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"delete failed: {str(e)}",
            "data": None
        }), 500


# SSE 登录接口
@app.route('/login')
def login():
    # 1 小红书 2 视频号 3 抖音 4 快手
    login_type = request.args.get('type')
    # 账号名
    account_id = request.args.get('id')

    if login_type not in {'1', '2', '3', '4'} or not account_id:
        return jsonify({"code": 400, "msg": "缺少或非法的平台类型/账号名称", "data": None}), 400

    # 模拟一个用于异步通信的队列
    status_queue = Queue()
    queue_key = f"{login_type}:{account_id}:{uuid.uuid4().hex[:8]}"
    with active_queues_lock:
        active_queues[queue_key] = status_queue

    # 启动异步任务线程
    thread = threading.Thread(target=run_async_function, args=(login_type, account_id, status_queue), daemon=True)
    thread.start()
    response = Response(sse_stream(status_queue, queue_key=queue_key), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'  # 关键：禁用 Nginx 缓冲
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Connection'] = 'keep-alive'
    return response

@app.route('/postVideo', methods=['POST'])
def postVideo():
    # 获取JSON数据
    data = request.get_json()

    if not data:
        return jsonify({"code": 400, "msg": "请求数据不能为空", "data": None}), 400

    # 从JSON数据中提取fileList和accountList
    file_list = data.get('fileList', [])
    account_list = data.get('accountList', [])
    type = data.get('type')
    title = data.get('title')
    tags = data.get('tags')
    category = data.get('category')
    enableTimer = data.get('enableTimer')
    if category == 0:
        category = None
    productLink = data.get('productLink', '')
    productTitle = data.get('productTitle', '')
    thumbnail_path = data.get('thumbnail', '')
    is_draft = data.get('isDraft', False)  # 新增参数：是否保存为草稿

    videos_per_day = data.get('videosPerDay')
    daily_times = data.get('dailyTimes')
    start_days = data.get('startDays')

    # 参数校验
    if not file_list:
        return jsonify({"code": 400, "msg": "文件列表不能为空", "data": None}), 400
    if not account_list:
        return jsonify({"code": 400, "msg": "账号列表不能为空", "data": None}), 400
    if not type:
        return jsonify({"code": 400, "msg": "平台类型不能为空", "data": None}), 400
    if not title:
        return jsonify({"code": 400, "msg": "标题不能为空", "data": None}), 400

    # 打印获取到的数据（仅作为示例）
    print("File List:", file_list)
    print("Account List:", account_list)

    try:
        match type:
            case 1:
                post_video_xhs(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                                   start_days)
            case 2:
                post_video_tencent(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                                   start_days, is_draft)
            case 3:
                post_video_DouYin(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                          start_days, thumbnail_path, productLink, productTitle)
            case 4:
                post_video_ks(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                          start_days)
            case _:
                return jsonify({"code": 400, "msg": f"不支持的平台类型: {type}", "data": None}), 400

        # 返回响应给客户端
        record_publish_history(
            type, title, file_list, account_list, tags,
            enableTimer, videos_per_day, daily_times, start_days,
            is_draft, 'success', '发布任务已提交'
        )
        return jsonify(
            {
                "code": 200,
                "msg": "发布任务已提交",
                "data": None
            }), 200
    except Exception as e:
        print(f"发布视频时出错: {str(e)}")
        try:
            record_publish_history(
                type, title, file_list, account_list, tags,
                enableTimer, videos_per_day, daily_times, start_days,
                is_draft, 'error', str(e)
            )
        except Exception:
            pass
        return jsonify({
            "code": 500,
            "msg": f"发布失败: {str(e)}",
            "data": None
        }), 500


@app.route('/updateUserinfo', methods=['POST'])
def updateUserinfo():
    # 获取JSON数据
    data = request.get_json()

    # 从JSON数据中提取 type 和 userName
    user_id = data.get('id')
    type = data.get('type')
    userName = data.get('userName')
    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 更新数据库记录
            cursor.execute('''
                           UPDATE user_info
                           SET type     = ?,
                               userName = ?
                           WHERE id = ?;
                           ''', (type, userName, user_id))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "account update successfully",
            "data": None
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("update failed!"),
            "data": None
        }), 500

@app.route('/postVideoBatch', methods=['POST'])
def postVideoBatch():
    data_list = request.get_json()

    if not isinstance(data_list, list):
        return jsonify({"code": 400, "msg": "Expected a JSON array", "data": None}), 400
    for data in data_list:
        # 从JSON数据中提取fileList和accountList
        file_list = data.get('fileList', [])
        account_list = data.get('accountList', [])
        type = data.get('type')
        title = data.get('title')
        tags = data.get('tags')
        category = data.get('category')
        enableTimer = data.get('enableTimer')
        if category == 0:
            category = None
        productLink = data.get('productLink', '')
        productTitle = data.get('productTitle', '')
        thumbnail_path = data.get('thumbnail', '')
        is_draft = data.get('isDraft', False)

        videos_per_day = data.get('videosPerDay')
        daily_times = data.get('dailyTimes')
        start_days = data.get('startDays')
        # 打印获取到的数据（仅作为示例）
        print("File List:", file_list)
        print("Account List:", account_list)
        try:
            match type:
                case 1:
                    post_video_xhs(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                                   start_days)
                case 2:
                    post_video_tencent(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                                       start_days, is_draft)
                case 3:
                    post_video_DouYin(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                              start_days, thumbnail_path, productLink, productTitle)
                case 4:
                    post_video_ks(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                              start_days)
            record_publish_history(
                type, title, file_list, account_list, tags,
                enableTimer, videos_per_day, daily_times, start_days,
                is_draft, 'success', '批量发布任务已提交'
            )
        except Exception as e:
            record_publish_history(
                type, title, file_list, account_list, tags,
                enableTimer, videos_per_day, daily_times, start_days,
                is_draft, 'error', str(e)
            )
            raise
    # 返回响应给客户端
    return jsonify(
        {
            "code": 200,
            "msg": None,
            "data": None
        }), 200


@app.route('/getPublishHistory', methods=['GET'])
def get_publish_history():
    ensure_runtime_ready()
    try:
        raw_limit = int(request.args.get('limit', 50) or 50)
    except (TypeError, ValueError):
        raw_limit = 50
    limit = min(max(raw_limit, 1), 200)
    platform_map = {1: '小红书', 2: '视频号', 3: '抖音', 4: '快手'}
    db_path = Path(BASE_DIR / "db" / "database.db")
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        rows = cursor.execute(
            '''
            SELECT id, platform_type, title, file_list, account_list, tags,
                   enable_timer, schedule_summary, is_draft, status, message, created_at
            FROM publish_records
            ORDER BY id DESC
            LIMIT ?
            ''',
            (limit,),
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item['platform_name'] = platform_map.get(item['platform_type'], f"平台({item['platform_type']})")
        for field in ('file_list', 'account_list', 'tags'):
            try:
                item[field] = json.loads(item[field] or '[]')
            except Exception:
                item[field] = []
        result.append(item)
    return jsonify({"code": 200, "msg": "success", "data": result}), 200


@app.route('/deletePublishRecord', methods=['GET'])
def delete_publish_record():
    ensure_runtime_ready()
    record_id = request.args.get('id')
    if not record_id:
        return jsonify({"code": 400, "msg": "缺少记录 ID", "data": None}), 400
    db_path = Path(BASE_DIR / "db" / "database.db")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM publish_records WHERE id = ?", (record_id,))
        conn.commit()
    return jsonify({"code": 200, "msg": "删除成功", "data": None}), 200


@app.route('/getTitleTemplates', methods=['GET'])
def get_title_templates():
    ensure_runtime_ready()
    category = (request.args.get('category') or '').strip()
    keyword = (request.args.get('keyword') or '').strip()
    db_path = Path(BASE_DIR / "db" / "database.db")
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        sql = "SELECT id, category, title, tags, note, use_count, created_at FROM title_templates WHERE 1=1"
        params = []
        if category and category != '全部':
            sql += " AND category = ?"
            params.append(category)
        if keyword:
            sql += " AND (title LIKE ? OR note LIKE ? OR tags LIKE ?)"
            like = f"%{keyword}%"
            params.extend([like, like, like])
        sql += " ORDER BY id DESC"
        rows = cursor.execute(sql, params).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        try:
            item['tags'] = json.loads(item['tags'] or '[]')
        except Exception:
            item['tags'] = []
        items.append(item)
    return jsonify({"code": 200, "msg": "success", "data": items}), 200


@app.route('/saveTitleTemplate', methods=['POST'])
def save_title_template():
    ensure_runtime_ready()
    data = request.get_json(silent=True) or {}
    tpl_id = data.get('id')
    category = str(data.get('category') or '通用').strip() or '通用'
    title = str(data.get('title') or '').strip()
    note = str(data.get('note') or '').strip()
    raw_tags = data.get('tags') or []
    if isinstance(raw_tags, str):
        tags = [t.strip().lstrip('#') for t in raw_tags.replace('，', ',').split(',') if t.strip()]
    elif isinstance(raw_tags, list):
        tags = [str(t).strip().lstrip('#') for t in raw_tags if str(t).strip()]
    else:
        tags = []

    if not title:
        return jsonify({"code": 400, "msg": "标题内容不能为空", "data": None}), 400

    db_path = Path(BASE_DIR / "db" / "database.db")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        if tpl_id:
            cursor.execute(
                "UPDATE title_templates SET category = ?, title = ?, tags = ?, note = ? WHERE id = ?",
                (category, title, json.dumps(tags, ensure_ascii=False), note, tpl_id),
            )
        else:
            cursor.execute(
                "INSERT INTO title_templates (category, title, tags, note) VALUES (?, ?, ?, ?)",
                (category, title, json.dumps(tags, ensure_ascii=False), note),
            )
            tpl_id = cursor.lastrowid
        conn.commit()
    return jsonify({"code": 200, "msg": "保存成功", "data": {"id": tpl_id}}), 200


@app.route('/deleteTitleTemplate', methods=['GET'])
def delete_title_template():
    ensure_runtime_ready()
    tpl_id = request.args.get('id')
    if not tpl_id:
        return jsonify({"code": 400, "msg": "缺少模板 ID", "data": None}), 400
    db_path = Path(BASE_DIR / "db" / "database.db")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM title_templates WHERE id = ?", (tpl_id,))
        conn.commit()
    return jsonify({"code": 200, "msg": "删除成功", "data": None}), 200

# Cookie文件上传API
@app.route('/uploadCookie', methods=['POST'])
def upload_cookie():
    try:
        if 'file' not in request.files:
            return jsonify({
                "code": 400,
                "msg": "没有找到Cookie文件",
                "data": None
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "code": 400,
                "msg": "Cookie文件名不能为空",
                "data": None
            }), 400

        if not file.filename.endswith('.json'):
            return jsonify({
                "code": 400,
                "msg": "Cookie文件必须是JSON格式",
                "data": None
            }), 400

        # 获取账号信息
        account_id = request.form.get('id')
        platform = request.form.get('platform')

        if not account_id or not platform:
            return jsonify({
                "code": 400,
                "msg": "缺少账号ID或平台信息",
                "data": None
            }), 400

        # 从数据库获取账号的文件路径
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT filePath FROM user_info WHERE id = ?', (account_id,))
            result = cursor.fetchone()

        if not result:
            return jsonify({
                "code": 500,
                "msg": "账号不存在",
                "data": None
            }), 404

        # 保存上传的Cookie文件到对应路径
        cookie_file_path = Path(BASE_DIR / "cookiesFile" / result['filePath'])
        cookie_file_path.parent.mkdir(parents=True, exist_ok=True)

        file.save(str(cookie_file_path))

        # 更新数据库中的账号信息（可选，比如更新更新时间）
        # 这里可以根据需要添加额外的处理逻辑

        return jsonify({
            "code": 200,
            "msg": "Cookie文件上传成功",
            "data": None
        }), 200

    except Exception as e:
        print(f"上传Cookie文件时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"上传Cookie文件失败: {str(e)}",
            "data": None
        }), 500


# Cookie文件下载API
@app.route('/downloadCookie', methods=['GET'])
def download_cookie():
    try:
        file_path = request.args.get('filePath')
        if not file_path:
            return jsonify({
                "code": 500,
                "msg": "缺少文件路径参数",
                "data": None
            }), 400

        # 验证文件路径的安全性，防止路径遍历攻击
        cookie_file_path = Path(BASE_DIR / "cookiesFile" / file_path).resolve()
        base_path = Path(BASE_DIR / "cookiesFile").resolve()

        if not cookie_file_path.is_relative_to(base_path):
            return jsonify({
                "code": 500,
                "msg": "非法文件路径",
                "data": None
            }), 400

        if not cookie_file_path.exists():
            return jsonify({
                "code": 500,
                "msg": "Cookie文件不存在",
                "data": None
            }), 404

        # 返回文件
        return send_from_directory(
            directory=str(cookie_file_path.parent),
            path=cookie_file_path.name,
            as_attachment=True
        )

    except Exception as e:
        print(f"下载Cookie文件时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"下载Cookie文件失败: {str(e)}",
            "data": None
        }), 500


# 包装函数：在线程中运行异步函数
def run_async_function(type,id,status_queue):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        match type:
            case '1':
                loop.run_until_complete(xiaohongshu_cookie_gen(id, status_queue))
            case '2':
                loop.run_until_complete(get_tencent_cookie(id, status_queue))
            case '3':
                loop.run_until_complete(douyin_cookie_gen(id, status_queue))
            case '4':
                loop.run_until_complete(get_ks_cookie(id, status_queue))
            case _:
                status_queue.put("500")
    except Exception as e:
        print(f"❌ 登录任务异常 (type={type}, id={id}): {e}")
        status_queue.put("500")
    finally:
        loop.close()

# SSE 流生成器函数
def sse_stream(status_queue, queue_key=None, timeout_seconds=240):
    deadline = time.monotonic() + timeout_seconds
    last_keepalive = time.monotonic()
    try:
        while time.monotonic() < deadline:
            try:
                msg = status_queue.get(timeout=0.5)
            except Empty:
                if time.monotonic() - last_keepalive >= 15:
                    yield ": keepalive\n\n"
                    last_keepalive = time.monotonic()
                continue

            if msg is None:
                continue
            msg_str = str(msg)
            yield f"data: {msg_str}\n\n"
            if msg_str in {"200", "500"}:
                return

        yield "data: 500\n\n"
    finally:
        if queue_key:
            with active_queues_lock:
                active_queues.pop(queue_key, None)

if __name__ == '__main__':
    ensure_runtime_ready()
    app.run(host='0.0.0.0' ,port=5409)
