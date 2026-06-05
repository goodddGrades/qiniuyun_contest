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

# Windows GBK 编码兼容：强制 Flask 输出 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

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
    """确保所有响应使用 UTF-8 编码（解决 Windows GBK 问题）"""
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
    return script_id


def _load_script(script_id: str) -> dict | None:
    """按 ID 加载剧本"""
    filepath = STORAGE_DIR / f"{script_id}.yaml"
    if not filepath.exists():
        return None
    raw = filepath.read_text(encoding="utf-8")
    return yaml.safe_load(raw)


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
    """接收小说文本（粘贴或上传文件），执行转换"""
    title = request.form.get("title", "").strip() or "未命名作品"
    novel_text = ""

    # 优先读上传的文件
    uploaded_file = request.files.get("file")
    if uploaded_file and uploaded_file.filename:
        ext = Path(uploaded_file.filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return render_template(
                "index.html",
                error=f"不支持的文件格式：{ext}，支持：{', '.join(SUPPORTED_EXTENSIONS)}",
            )
        # 保存临时文件再读取
        tmp = STORAGE_DIR / uploaded_file.filename
        uploaded_file.save(str(tmp))
        novel_text = extract_text_from_file(tmp)
        tmp.unlink(missing_ok=True)
        title = title or Path(uploaded_file.filename).stem

    # 没有文件就取粘贴框的内容
    if not novel_text:
        novel_text = request.form.get("novel_text", "").strip()

    if not novel_text:
        return render_template("index.html", error="请粘贴小说内容或上传文件")

    # 执行转换
    converter = NovelConverter()
    result = converter.convert(novel_text, title=title)

    # 保存并跳转
    script_id = _save_script(result)
    return redirect(url_for("result", script_id=script_id))


@app.route("/result/<script_id>")
def result(script_id: str):
    """展示转换结果"""
    data = _load_script(script_id)
    if data is None:
        return render_template("index.html", error="剧本不存在或已过期")

    yaml_text = yaml.dump(data, allow_unicode=True, indent=2)
    return render_template("result.html", script_id=script_id, yaml=yaml_text)


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


@app.route("/download/<script_id>")
def download(script_id: str):
    """下载 YAML 文件"""
    filepath = STORAGE_DIR / f"{script_id}.yaml"
    if not filepath.exists():
        return render_template("index.html", error="剧本不存在或已过期")

    return send_file(
        filepath,
        mimetype="text/yaml",
        as_attachment=True,
        download_name=f"script_{script_id}.yaml",
    )


# -----------------------------------------------------------
# 启动
# -----------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
