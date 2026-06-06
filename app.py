"""
AI小说转剧本工具 - Flask Web 应用

核心路由：
  /          首页（上传小说）
  /convert   执行转换
  /result/   查看转换结果
  /editor/   编辑剧本
  /download/ 下载 YAML
"""

import io
import os
import sys
import uuid

import yaml
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_file,
    jsonify,
)

from config import Config
from novel_to_script.converter import NovelConverter

# -----------------------------------------------------------
# 支持的文件格式
# -----------------------------------------------------------
SUPPORTED_EXTENSIONS = {".txt", ".md", ".docx"}

# -----------------------------------------------------------
# 应用初始化
# -----------------------------------------------------------

app = Flask(__name__)
app.config.from_object(Config)

# Windows 兼容：所有响应强制 UTF-8 编码
app.config["JSON_AS_ASCII"] = False


@app.after_request
def force_utf8(response):
    """确保 HTML 响应使用 UTF-8 编码（解决 Windows GBK 问题），不影响文件下载"""
    if "text/html" in response.content_type:
        response.content_type = "text/html; charset=utf-8"
    return response


# 临时存储（生产环境应改用数据库）
STORAGE_DIR = Path("instance/scripts")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def extract_text_from_file(filepath: Path) -> str:
    """从不同格式的文件中提取文本内容"""
    ext = filepath.suffix.lower()

    if ext == ".docx":
        try:
            from docx import Document
            doc = Document(str(filepath))
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            return f"[错误：未安装 python-docx，无法读取 {filepath.name}]"

    # .txt / .md 直接以 UTF-8 读取
    return filepath.read_text(encoding="utf-8")


def _save_script(data: dict, script_id: str = "") -> str:
    """保存剧本到临时文件，返回 ID"""
    if not script_id:
        script_id = uuid.uuid4().hex[:12]
    filepath = STORAGE_DIR / f"{script_id}.yaml"
    filepath.write_text(yaml.dump(data, allow_unicode=True, indent=2), encoding="utf-8")
    # 额外存一份标题，方便下载用
    title = (data.get("剧本", {}).get("元数据", {})).get("标题", "剧本")
    STORAGE_DIR.joinpath(f"{script_id}.title").write_text(title, encoding="utf-8")
    return script_id


def _load_script(script_id: str) -> dict | None:
    """按 ID 加载剧本"""
    filepath = STORAGE_DIR / f"{script_id}.yaml"
    if not filepath.exists():
        return None
    raw = filepath.read_text(encoding="utf-8")
    return yaml.safe_load(raw)


# -----------------------------------------------------------
# 转换进度跟踪
# -----------------------------------------------------------
import threading

PROGRESS: dict[str, dict] = {}
CANCEL_EVENTS: dict[str, threading.Event] = {}
LOCK = threading.Lock()


class CancelledError(Exception):
    """转换被用户取消"""
    pass


def _split_into_episodes(acts: list, episode_count: int) -> list[dict]:
    """将幕列表平均切分为指定集数"""
    if episode_count <= 1 or len(acts) <= 1:
        return [{"name": "完整剧本", "acts": list(range(len(acts)))}]

    # 集数不能超过幕数，否则后面的集是空的
    episode_count = min(episode_count, len(acts))
    total = len(acts)
    base = total // episode_count
    remainder = total % episode_count
    episodes = []
    start = 0
    for i in range(episode_count):
        size = base + (1 if i < remainder else 0)
        indices = list(range(start, start + size))
        episodes.append({
            "name": f"第{i + 1}集",
            "acts": indices,
        })
        start += size
    return episodes


def _run_conversion(task_id: str, novel_text: str, title: str, episode_count: int = 0):
    """在后台线程中执行转换，逐步更新进度"""
    from novel_to_script.converter import NovelConverter

    def on_progress(current, total, message):
        # 每次回调都检查用户是否点了取消
        cancel_event = CANCEL_EVENTS.get(task_id)
        if cancel_event and cancel_event.is_set():
            raise CancelledError()
        status = "converting" if total > 0 and current > 0 else "analyzing"
        with LOCK:
            PROGRESS[task_id] = {
                "status": status,
                "current": current,
                "total": total,
                "message": message,
            }

    try:
        on_progress(0, 1, "正在分析小说...")
        converter = NovelConverter()
        result = converter.convert(novel_text, title=title, progress_callback=on_progress)

        with LOCK:
            PROGRESS[task_id] = {"status": "saving", "current": 1, "total": 1, "message": "正在保存剧本..."}

        script_id = _save_script(result)

        # 集数切分
        acts = result.get("剧本", {}).get("幕", [])
        episodes = _split_into_episodes(acts, episode_count)
        episode_path = STORAGE_DIR / f"{script_id}.episodes"
        episode_path.write_text(
            yaml.dump({"episodes": episodes, "count": episode_count},
                       allow_unicode=True, indent=2),
            encoding="utf-8",
        )

        with LOCK:
            PROGRESS[task_id] = {
                "status": "done", "current": 1, "total": 1,
                "message": "转换完成!", "result_id": script_id,
            }

    except CancelledError:
        with LOCK:
            PROGRESS[task_id] = {"status": "cancelled", "current": 0, "total": 0, "message": "已取消转换"}
    except Exception as e:
        with LOCK:
            PROGRESS[task_id] = {"status": "error", "current": 0, "total": 0, "message": f"转换失败: {e}"}


# -----------------------------------------------------------
# 路由
# -----------------------------------------------------------


@app.route("/")
def index():
    """首页 - 上传小说"""
    return render_template("index.html")


@app.route("/books")
def list_books():
    """列出 book/ 目录下所有小说"""
    book_dir = Path("book")
    if not book_dir.exists():
        return render_template("index.html", error="book/ 文件夹不存在，请在项目根目录创建")

    books = []
    for f in sorted(book_dir.iterdir()):
        if f.suffix.lower() in SUPPORTED_EXTENSIONS:
            size_kb = f.stat().st_size / 1024
            books.append({
                "name": f.name,
                "size": f"{size_kb:.0f} KB",
                "ext": f.suffix.lower(),
            })
    return render_template("books.html", books=books)


@app.route("/books/<path:filename>")
def read_book(filename: str):
    """读取 book/ 下指定小说内容"""
    filepath = Path("book") / filename
    if not filepath.exists() or filepath.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return render_template("index.html", error=f"文件不存在或格式不支持: {filename}")

    text = extract_text_from_file(filepath)
    title = filepath.stem
    return render_template(
        "index.html",
        preset_title=title,
        preset_text=text,
        from_book=filename,
    )


@app.route("/convert", methods=["POST"])
def convert():
    """接收小说文本（粘贴或上传文件），后台执行转换，跳转到进度页"""
    # 标题优先级：用户手动填写 > 上传文件名 > "未命名作品"
    manual_title = request.form.get("title", "").strip()
    novel_text = ""
    title = ""  # 先初始化空

    # 优先读上传的文件
    uploaded_file = request.files.get("file")
    if uploaded_file and uploaded_file.filename:
        ext = Path(uploaded_file.filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return render_template(
                "index.html",
                error=f"不支持的文件格式：{ext}，支持：{', '.join(SUPPORTED_EXTENSIONS)}",
            )
        tmp = STORAGE_DIR / uploaded_file.filename
        uploaded_file.save(str(tmp))
        novel_text = extract_text_from_file(tmp)
        tmp.unlink(missing_ok=True)
        # 用户没填标题才用文件名
        if manual_title:
            title = manual_title
        else:
            title = Path(uploaded_file.filename).stem

    if not novel_text:
        novel_text = request.form.get("novel_text", "").strip()

    if not novel_text:
        return render_template("index.html", error="请粘贴小说内容或上传文件")

    # 如果还没设标题（纯粘贴文本场景），fallback
    if not title:
        title = manual_title or "未命名作品"

    # 集数设置
    try:
        episode_count = int(request.form.get("episode_count", "0"))
    except ValueError:
        episode_count = 0

    # 创建任务 ID，启动后台转换
    task_id = uuid.uuid4().hex[:8]
    with LOCK:
        PROGRESS[task_id] = {"status": "queued", "current": 0, "total": 0, "message": "正在准备..."}

    thread = threading.Thread(
        target=_run_conversion,
        args=(task_id, novel_text, title, episode_count),
        daemon=True,
    )
    thread.start()

    return redirect(url_for("progress_page", task_id=task_id))


@app.route("/progress/<task_id>")
def progress_page(task_id: str):
    """转换进度页"""
    return render_template("progress.html", task_id=task_id)


@app.route("/progress/<task_id>/status")
def progress_status(task_id: str):
    """转换进度 API（JSON）"""
    with LOCK:
        data = PROGRESS.get(task_id, {"status": "not_found", "message": "任务不存在"})
    return jsonify(data)


@app.route("/progress/<task_id>/cancel", methods=["POST"])
def cancel_conversion(task_id: str):
    """取消正在进行的转换"""
    with LOCK:
        if task_id not in PROGRESS:
            return jsonify({"ok": False, "error": "任务不存在"}), 404
        status = PROGRESS[task_id].get("status", "")
        if status in ("done", "cancelled", "error"):
            return jsonify({"ok": False, "error": f"任务已{status}，无法取消"}), 400

        # 设置取消标志
        event = CANCEL_EVENTS.setdefault(task_id, threading.Event())
        event.set()
        PROGRESS[task_id] = {"status": "cancelling", "current": 0, "total": 0, "message": "正在取消..."}

    return jsonify({"ok": True, "message": "取消请求已发送"})


@app.route("/result/<script_id>")
@app.route("/result/<script_id>/<int:episode>")
def result(script_id: str, episode: int = 0):
    """展示转换结果（可选指定集数）"""
    data = _load_script(script_id)
    if data is None:
        return render_template("index.html", error="剧本不存在或已过期")

    # 读取集信息
    episode_path = STORAGE_DIR / f"{script_id}.episodes"
    episodes = []
    if episode_path.exists():
        ep_data = yaml.safe_load(episode_path.read_text(encoding="utf-8"))
        episodes = ep_data.get("episodes", [])
        episode = min(episode, len(episodes) - 1) if episodes else 0

    acts = data.get("剧本", {}).get("幕", [])

    # 预计算所有集的 YAML（用于 JS 无刷新切换）
    full_yaml = yaml.dump(data, allow_unicode=True, indent=2)
    episode_yamls = {"-1": full_yaml}  # -1 = 完整剧本
    if episodes:
        for i, ep in enumerate(episodes):
            filtered_acts = [acts[j] for j in ep["acts"] if j < len(acts)]
            filtered = {"剧本": {**data["剧本"], "幕": filtered_acts}}
            episode_yamls[str(i)] = yaml.dump(filtered, allow_unicode=True, indent=2)

    # 当前选中的集
    if episodes and episode > 0:
        ep_info = episodes[episode]
        filtered_acts = [acts[j] for j in ep_info["acts"] if j < len(acts)]
        filtered = {"剧本": {**data["剧本"], "幕": filtered_acts}}
        yaml_text = yaml.dump(filtered, allow_unicode=True, indent=2)
    else:
        yaml_text = yaml.dump(data, allow_unicode=True, indent=2)

    return render_template(
        "result.html",
        script_id=script_id,
        yaml=yaml_text,
        episodes=episodes,
        current_episode=episode,
        episode_yamls=episode_yamls,
    )


@app.route("/editor/<script_id>")
def editor(script_id: str):
    """编辑剧本"""
    data = _load_script(script_id)
    if data is None:
        return render_template("index.html", error="剧本不存在或已过期")

    yaml_text = yaml.dump(data, allow_unicode=True, indent=2)
    return render_template("editor.html", script_id=script_id, yaml=yaml_text)


@app.route("/editor/<script_id>/save", methods=["POST"])
def save_editor(script_id: str):
    """保存编辑后的 YAML"""
    yaml_text = request.form.get("yaml_text", "").strip()
    if not yaml_text:
        return jsonify({"ok": False, "error": "内容为空"}), 400

    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        return jsonify({"ok": False, "error": f"YAML 语法错误: {e}"}), 400

    _save_script(data, script_id)
    return jsonify({"ok": True})


def _get_title(script_id: str) -> str:
    """读取保存的剧本标题"""
    title_file = STORAGE_DIR / f"{script_id}.title"
    return title_file.read_text(encoding="utf-8") if title_file.exists() else "剧本"


def _safe_filename(title: str, suffix: str = "剧本") -> str:
    """生成安全的文件名"""
    safe = "".join(c for c in title if c.isalnum() or c in " _-（()）").strip() or "剧本"
    return f"{safe}_{suffix}.yaml"


@app.route("/download/<script_id>")
def download(script_id: str):
    """下载完整剧本 YAML"""
    filepath = STORAGE_DIR / f"{script_id}.yaml"
    if not filepath.exists():
        return render_template("index.html", error="剧本不存在或已过期")

    title = _get_title(script_id)
    return send_file(
        filepath,
        mimetype="text/yaml",
        as_attachment=True,
        download_name=_safe_filename(title),
    )


@app.route("/download/<script_id>/episode/<int:episode>")
def download_episode(script_id: str, episode: int):
    """下载指定集的 YAML（内存流，不写临时文件）"""
    data = _load_script(script_id)
    if data is None:
        return render_template("index.html", error="剧本不存在或已过期")

    ep_path = STORAGE_DIR / f"{script_id}.episodes"
    if not ep_path.exists():
        return download(script_id)

    ep_data = yaml.safe_load(ep_path.read_text(encoding="utf-8"))
    episodes = ep_data.get("episodes", [])
    if episode < 0 or episode >= len(episodes):
        return download(script_id)

    ep_info = episodes[episode]
    acts = data.get("剧本", {}).get("幕", [])
    filtered = {"剧本": {**data["剧本"], "幕": [acts[i] for i in ep_info["acts"] if i < len(acts)]}}

    buf = io.BytesIO()
    buf.write(yaml.dump(filtered, allow_unicode=True, indent=2).encode("utf-8"))
    buf.seek(0)

    title = _get_title(script_id)
    return send_file(
        buf,
        mimetype="text/yaml",
        as_attachment=True,
        download_name=_safe_filename(title, ep_info["name"]),
    )


# -----------------------------------------------------------
# 启动
# -----------------------------------------------------------

if __name__ == "__main__":
    import io
    # Windows 编码兼容: 只在直接启动时生效, 不影响 pytest
    if hasattr(sys.stdout, "buffer"):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
        except Exception:
            pass
    app.run(debug=True, port=5000)
