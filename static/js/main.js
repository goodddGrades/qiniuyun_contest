/**
 * AI 小说转剧本工具 - 前端脚本
 */

document.addEventListener("DOMContentLoaded", () => {
    // 自动调整编辑器高度
    const editor = document.getElementById("yamlEditor");
    if (editor) {
        editor.addEventListener("input", () => {
            editor.style.height = "auto";
            editor.style.height = editor.scrollHeight + "px";
        });
    }
});
