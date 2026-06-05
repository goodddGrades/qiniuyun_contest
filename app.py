"""
AI小说转剧本工具 - Flask Web 应用

核心路由：
  /          首页（上传小说）
  /convert   执行转换
  /result/   查看转换结果
  /editor/   编辑剧本
  /download/ 下载 YAML
"""

import uuid
import yaml
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file,
    jsonify,
)

from config import Config
from novel_to_script.converter import NovelConverter

# -----------------------------------------------------------
# 应用初始化
# -----------------------------------------------------------

app = Flask(__name__)
app.config.from_object(Config)

# 临时存储（生产环境应改用数据库）
STORAGE_DIR = Path("instance/scripts")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _save_script(data: dict) -> str:
    """保存剧本到临时文件，返回 ID"""
    script_id = uuid.uuid4().hex[:12]
    filepath = STORAGE_DIR / f"{script_id}.yaml"
    filepath.write_text(yaml.dump(data, allow_unicode=True, indent=2))
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


@app.route("/convert", methods=["POST"])
def convert():
    """接收小说文本，执行转换"""
    novel_text = request.form.get("novel_text", "").strip()
    title = request.form.get("title", "").strip() or "未命名作品"

    if not novel_text:
        return render_template("index.html", error="请粘贴小说内容")

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

    _save_script(data)  # overwrites same id
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
