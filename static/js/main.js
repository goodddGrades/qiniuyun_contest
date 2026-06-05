/**
 * AI 小说转剧本工具 — 前端交互脚本
 * 功能：打字机动画、拖拽上传、加载状态、一键复制、编辑器快捷键
 */

document.addEventListener("DOMContentLoaded", () => {

    // ============================================================
    // 1. 打字机标题效果（降级方案：页面加载后清除闪烁光标）
    // ============================================================
    const typewriter = document.querySelector(".typewriter-title");
    if (typewriter) {
        // 打字机动画结束后，保留光标闪烁，不做额外操作
        // 但如果屏幕宽度 < 768px，CSS 已经禁用了打字机效果
    }

    // ============================================================
    // 2. 拖拽上传区
    // ============================================================
    const dropZone = document.querySelector(".drop-zone");
    const textarea = document.getElementById("novel_text");
    const uploadForm = document.getElementById("uploadForm");

    if (dropZone && textarea) {
        // 点击拖拽区聚焦到 textarea
        dropZone.addEventListener("click", () => {
            textarea.focus();
            textarea.scrollIntoView({ behavior: "smooth", block: "center" });
        });

        // 拖拽 hover 效果
        dropZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropZone.classList.add("drag-over");
        });

        dropZone.addEventListener("dragleave", () => {
            dropZone.classList.remove("drag-over");
        });

        dropZone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropZone.classList.remove("drag-over");

            const file = e.dataTransfer.files[0];
            if (file && (file.type === "text/plain" || file.name.endsWith(".txt"))) {
                const reader = new FileReader();
                reader.onload = (ev) => {
                    textarea.value = ev.target.result;
                    // 触发输入事件以便检测章节数
                    textarea.dispatchEvent(new Event("input"));
                    showNotification(`✅ 已加载文件: ${file.name}`, "success");
                };
                reader.readAsText(file, "UTF-8");
            } else if (file) {
                showNotification("❌ 仅支持 .txt 文本文件", "error");
            }
        });
    }

    // ============================================================
    // 3. 章节数检测（实时统计 "第X章" 数量）
    // ============================================================
    const chapterCountDisplay = document.getElementById("chapterCount");
    if (textarea && chapterCountDisplay) {
        const countChapters = () => {
            const text = textarea.value;
            // 匹配 "第X章" 或 "Chapter X" 或 "第X节" 等
            const matches = text.match(/(第[一二三四五六七八九十百千万\d]+[章章节节回回]|Chapter\s+\d+)/gi);
            const count = matches ? matches.length : 0;
            chapterCountDisplay.textContent = `已检测到 ${count} 个章节`;
            chapterCountDisplay.className = count >= 3 ? "chapter-count ok" : "chapter-count warn";
            return count;
        };

        textarea.addEventListener("input", countChapters);
        // 初始统计
        countChapters();
    }

    // ============================================================
    // 4. 表单提交 — 加载状态指示器
    // ============================================================
    if (uploadForm) {
        const submitBtn = uploadForm.querySelector(".btn-primary");

        uploadForm.addEventListener("submit", (e) => {
            const novelText = document.getElementById("novel_text");
            if (!novelText || !novelText.value.trim()) {
                e.preventDefault();
                showNotification("❌ 请粘贴小说内容", "error");
                return;
            }

            // 显示加载状态
            submitBtn.classList.add("btn-loading");
            submitBtn.disabled = true;

            // 显示全屏加载遮罩
            const overlay = document.getElementById("loadingOverlay");
            if (overlay) {
                overlay.classList.add("active");
            }

            // 表单正常提交，由后端重定向
        });
    }

    // ============================================================
    // 5. 一键复制 YAML
    // ============================================================
    const copyBtn = document.getElementById("copyYamlBtn");
    const yamlCode = document.getElementById("yamlCode");

    if (copyBtn && yamlCode) {
        copyBtn.addEventListener("click", async () => {
            try {
                await navigator.clipboard.writeText(yamlCode.textContent);
                copyBtn.textContent = "✅ 已复制";
                copyBtn.classList.add("copied");
                setTimeout(() => {
                    copyBtn.textContent = "📋 复制";
                    copyBtn.classList.remove("copied");
                }, 2000);
            } catch {
                // 降级方案：使用 textarea
                const ta = document.createElement("textarea");
                ta.value = yamlCode.textContent;
                document.body.appendChild(ta);
                ta.select();
                document.execCommand("copy");
                document.body.removeChild(ta);
                copyBtn.textContent = "✅ 已复制";
                copyBtn.classList.add("copied");
                setTimeout(() => {
                    copyBtn.textContent = "📋 复制";
                    copyBtn.classList.remove("copied");
                }, 2000);
            }
        });
    }

    // ============================================================
    // 6. 编辑器 — Ctrl+S 保存快捷键
    // ============================================================
    const yamlEditor = document.getElementById("yamlEditor");
    const saveBtn = document.getElementById("saveBtn");

    if (yamlEditor && saveBtn) {
        // Ctrl+S / Cmd+S 触发保存
        yamlEditor.addEventListener("keydown", (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === "s") {
                e.preventDefault();
                saveBtn.click();
            }
        });

        // 自动调整编辑器高度
        yamlEditor.addEventListener("input", () => {
            yamlEditor.style.height = "auto";
            yamlEditor.style.height = Math.min(yamlEditor.scrollHeight, window.innerHeight * 0.8) + "px";
        });

        // 初始调整
        setTimeout(() => {
            yamlEditor.style.height = "auto";
            yamlEditor.style.height = Math.min(yamlEditor.scrollHeight, window.innerHeight * 0.8) + "px";
        }, 100);
    }

    // ============================================================
    // 7. 通知系统（轻量 Toast）
    // ============================================================
    function showNotification(message, type = "info") {
        // 移除旧通知
        const old = document.querySelector(".toast-notification");
        if (old) old.remove();

        const toast = document.createElement("div");
        toast.className = `toast-notification toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        // 显示
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
    // 8. Toast 通知样式（动态注入，避免重复）
    // ============================================================
    if (!document.getElementById("toastStyles")) {
        const style = document.createElement("style");
        style.id = "toastStyles";
        style.textContent = `
            .toast-notification {
                position: fixed;
                bottom: 32px;
                left: 50%;
                transform: translateX(-50%) translateY(20px);
                padding: 14px 24px;
                border-radius: 12px;
                font-family: 'DM Sans', sans-serif;
                font-size: 0.9rem;
                font-weight: 500;
                z-index: 9999;
                opacity: 0;
                transition: all 0.3s ease;
                pointer-events: none;
                backdrop-filter: blur(12px);
                border: 1px solid var(--border-subtle, rgba(212,168,83,0.12));
            }
            .toast-notification.toast-visible {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
            .toast-success {
                background: rgba(34, 197, 94, 0.15);
                color: #22c55e;
                border-color: rgba(34, 197, 94, 0.2);
            }
            .toast-error {
                background: rgba(239, 68, 68, 0.15);
                color: #ef4444;
                border-color: rgba(239, 68, 68, 0.2);
            }
            .toast-info {
                background: rgba(96, 165, 250, 0.15);
                color: #60a5fa;
                border-color: rgba(96, 165, 250, 0.2);
            }
        `;
        document.head.appendChild(style);
    }

});