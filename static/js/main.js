/**
 * AI 小说转剧本工具 - 前端交互脚本
 * 功能：拖拽上传 / 章节统计 / 一键复制 / 快捷键 / Toast 通知
 */

document.addEventListener("DOMContentLoaded", () => {
    // ============================================================
    // 1. 拖拽上传（index.html）
    // ============================================================
    const dropZone = document.getElementById("dropZone");
    const novelText = document.getElementById("novel_text");

    if (dropZone && novelText) {
        // 阻止默认拖拽行为
        ["dragenter", "dragover", "dragleave", "drop"].forEach((evt) => {
            dropZone.addEventListener(evt, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        // 拖拽悬停高亮
        ["dragenter", "dragover"].forEach((evt) => {
            dropZone.addEventListener(evt, () => {
                dropZone.classList.add("drag-over");
            });
        });

        ["dragleave", "drop"].forEach((evt) => {
            dropZone.addEventListener(evt, () => {
                dropZone.classList.remove("drag-over");
            });
        });

        // 放下文件 → 读取 .txt 内容
        dropZone.addEventListener("drop", (e) => {
            const files = e.dataTransfer.files;
            if (files.length === 0) return;

            const file = files[0];
            if (!file.name.endsWith(".txt")) {
                showToast("请拖拽 .txt 文件", "error");
                return;
            }

            const reader = new FileReader();
            reader.onload = (event) => {
                novelText.value = event.target.result;
                updateChapterCount();
                showToast(`✅ 已加载: ${file.name}`, "success");
            };
            reader.readAsText(file, "UTF-8");
        });

        // 点击拖拽区定位到 textarea
        dropZone.addEventListener("click", () => novelText.focus());

        // 实时章节统计
        novelText.addEventListener("input", updateChapterCount);
    }

    // ============================================================
    // 2. 章节数量统计
    // ============================================================
    function updateChapterCount() {
        const chapterCount = document.getElementById("chapterCount");
        if (!chapterCount || !novelText) return;

        const text = novelText.value;
        // 匹配「第X章」「第X节」「Chapter X」「CHAPTER X」
        const matches = text.match(/(第[一二三四五六七八九十百千万\d]+[章节]|Chapter\s*\d+|CHAPTER\s*\d+)/g);
        const count = matches ? matches.length : 0;

        if (count === 0) {
            chapterCount.textContent = "⚠️ 未检测到章节，请用「第X章」分隔";
            chapterCount.style.color = "var(--error)";
        } else if (count < 3) {
            chapterCount.textContent = `⚠️ 仅 ${count} 个章节，建议至少 3 章`;
            chapterCount.style.color = "var(--gold-primary)";
        } else {
            chapterCount.textContent = `✅ 已检测 ${count} 个章节`;
            chapterCount.style.color = "var(--success)";
        }
    }

    // 页面加载时初始化章节统计
    updateChapterCount();

    // ============================================================
    // 3. 提交按钮加载状态（index.html）
    // ============================================================
    const uploadForm = document.getElementById("uploadForm");
    const loadingOverlay = document.getElementById("loadingOverlay");
    const navLoading = document.getElementById("navLoading");

    if (uploadForm && loadingOverlay) {
        uploadForm.addEventListener("submit", () => {
            loadingOverlay.classList.add("active");
            if (navLoading) navLoading.classList.add("active");
        });
    }

    // ============================================================
    // 4. 一键复制 YAML（result.html）
    // ============================================================
    const copyBtn = document.getElementById("copyYamlBtn");
    const yamlCode = document.getElementById("yamlCode");

    if (copyBtn && yamlCode) {
        copyBtn.addEventListener("click", async () => {
            try {
                // 获取纯文本（去掉 HTML 标签）
                const text = yamlCode.textContent || yamlCode.innerText;
                await navigator.clipboard.writeText(text);

                copyBtn.classList.add("copied");
                copyBtn.textContent = "✅ 已复制";

                setTimeout(() => {
                    copyBtn.classList.remove("copied");
                    copyBtn.textContent = "📋 复制";
                }, 2000);
            } catch (e) {
                showToast("复制失败，请手动选择文本复制", "error");
            }
        });
    }

    // ============================================================
    // 5. Toast 通知系统
    // ============================================================
    function showToast(message, type = "info") {
        const existing = document.querySelector(".toast");
        if (existing) existing.remove();

        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        // 触发进场动画
        requestAnimationFrame(() => {
            toast.classList.add("toast-visible");
        });

        // 3秒后移除
        setTimeout(() => {
            toast.classList.remove("toast-visible");
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // ============================================================
    // 6. 编辑器快捷键 Ctrl+S 保存（editor.html）
    // ============================================================
    const yamlEditor = document.getElementById("yamlEditor");
    const saveBtn = document.getElementById("saveBtn");

    if (yamlEditor) {
        yamlEditor.addEventListener("keydown", (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === "s") {
                e.preventDefault();
                if (saveBtn) saveBtn.click();
            }
        });

        // 自动调整编辑器高度
        yamlEditor.addEventListener("input", () => {
            yamlEditor.style.height = "auto";
            yamlEditor.style.height = yamlEditor.scrollHeight + "px";
        });
    }
});