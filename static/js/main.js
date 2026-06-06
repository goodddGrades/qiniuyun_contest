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

        // 放下文件 → 读取内容
        dropZone.addEventListener("drop", (e) => {
            const files = e.dataTransfer.files;
            if (files.length === 0) return;

            const file = files[0];
            const ext = file.name.split('.').pop().toLowerCase();

            if (!["txt", "md", "docx"].includes(ext)) {
                showToast("请拖拽 .txt / .md / .docx 文件", "error");
                return;
            }

            if (ext === "docx") {
                // .docx 是二进制格式，设到文件上传 input 上
                const fileInput = document.getElementById("fileInput");
                if (fileInput) {
                    const dt = new DataTransfer();
                    dt.items.add(file);
                    fileInput.files = dt.files;
                    // 文本框显示提示
                    if (novelText) {
                        novelText.value = `（已选择 .docx 文件：${file.name}，点击「开始转换」即可上传处理）`;
                    }
                    showToast(`📄 已选择: ${file.name}，点击「开始转换」上传`, "success");
                }
                return;
            }

            // .txt / .md 直接读文本
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
        copyBtn.addEventListener("click", function () {
            const text = yamlCode.textContent || yamlCode.innerText;

            // 方案A：Clipboard API（现代浏览器，需要 HTTPS/localhost）
            function copyModern() {
                return navigator.clipboard.writeText(text).then(() => true).catch(() => false);
            }

            // 方案B：传统 execCommand 回退（所有浏览器，包括 HTTP）
            function copyLegacy() {
                try {
                    const ta = document.createElement("textarea");
                    ta.value = text;
                    ta.style.position = "fixed";
                    ta.style.left = "-9999px";
                    ta.style.top = "-9999px";
                    document.body.appendChild(ta);
                    ta.focus();
                    ta.select();
                    const ok = document.execCommand("copy");
                    document.body.removeChild(ta);
                    return ok;
                } catch (_) {
                    return false;
                }
            }

            // 先试 A，失败换 B，都不行给提示
            copyModern().then((ok) => {
                if (ok) return true;
                return copyLegacy();
            }).then((ok) => {
                if (ok) {
                    copyBtn.textContent = "✅ 已复制";
                    copyBtn.classList.add("copied");
                    showToast("✅ 已复制到剪贴板", "success");
                    setTimeout(() => {
                        copyBtn.textContent = "📋 复制";
                        copyBtn.classList.remove("copied");
                    }, 2000);
                } else {
                    showToast("⚠️ 复制失败，请按 Ctrl+C 手动复制", "error");
                }
            });
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

    // ============================================================
    // 7. 加载示例小说（index.html）
    // ============================================================
    const loadSampleBtn = document.getElementById("loadSampleBtn");

    if (loadSampleBtn && novelText) {
        const SAMPLE_NOVEL = [
            "第1章 迷雾中的身影",
            "",
            "林夜从没想过，自己会在凌晨三点的地铁站遇见一个死人。",
            "",
            "那是深秋的最后一个夜晚，冷风裹着枯叶在地铁口打转。林夜刚结束一场不愉快的采访——他本想挖出市长贪污的证据，却被安保\u201C客气\u201D地请了出来。他叼着烟，站在空荡荡的站台上，等着最后一班地铁。",
            "",
            "列车进站，车厢里只有两个乘客。一个戴耳机的年轻女孩，和一个裹着黑色风衣的中年男人。林夜没在意，找了个角落坐下，翻开笔记本整理今天的采访记录。",
            "",
            "但很快他就注意到了不对劲——那个中年男人一动不动地靠在座位上，姿势僵直得像是被钉在了椅子上。列车到站时，女孩匆匆下车，男人却没动。",
            "",
            "林夜走过去拍了拍他的肩膀。",
            "",
            "男人的身体像一堵墙一样，直挺挺地倒了下去。他的眼睛睁得很大，瞳孔里映着车厢惨白的灯光。死了至少两个小时了。",
            "",
            "林夜的第一个念头不是报警，而是：这张脸我见过。",
            "",
            "他掏出手机，翻出三个月前拍的一张照片——在一次秘密采访中，有人塞给他一张纸条，上面是一个男人的照片和一行字：\"查他，他是关键。\"纸条上的那张脸，和眼前这张死人的脸，一模一样。",
            "",
            "林夜的手开始发抖。",
            "",
            "他拨了110，但在电话接通的前一秒，他挂断了。因为他突然想起一件事——那个戴耳机的女孩，她全程没看过那具尸体一眼。一个正常人旁边倒着一具尸体，怎么可能毫无反应？",
            "",
            "",
            "第2章 消失的目击者",
            "",
            "林夜没有回家。他直接去了报社，把自己锁在资料室里，彻夜翻查那个死者的信息。",
            "",
            "死者叫陈远志，45岁，生前是市环保局的一名中层干部。三年前曾实名举报过一家化工厂偷排污水，举报信石沉大海，两个月后他被调到了一个闲职。从那之后，陈远志就没有在任何公开场合出现过。",
            "",
            "林夜调出了那封举报信的扫描件。信的措辞非常克制，但有几行字被反复涂改——\"他们不只是排污……他们在掩盖一些东西……\"后面被涂黑了，看不清具体内容。",
            "",
            "林夜猛吸了一口烟。",
            "",
            "他决定去找那个戴耳机的女孩。可是地铁站没有监控——上周刚被\u201C维修\u201D。他只能凭记忆画了一幅她的素描，发到了自己的朋友圈，附了一行字：\"寻人，有线索请私信。\"",
            "",
            "消息刚发出去三分钟，他的手机就响了。来电显示是一个陌生号码。",
            "",
            "\"你是林夜？\"对面是个女人的声音，嗓音很低，带着一丝沙哑。",
            "",
            "\"是我。\"",
            "",
            "\"你在地铁上见到的那个人，是不是戴着一条银色的十字架项链？\"",
            "",
            "林夜一愣。他没注意到项链。但他还没来得及回答，电话那头传来一阵刺耳的电流声，然后挂断了。",
            "",
            "他回拨过去——无人接听。",
            "",
            "林夜猛地站起来，抓起外套冲出了报社。他有种强烈的预感：那个女人就是戴耳机的女孩。而且她认识陈远志。",
            "",
            "",
            "第3章 暗处的眼睛",
            "",
            "第二天一早，林夜被一个电话吵醒。他发现自己居然在出租车上睡着了，手机屏幕上显示着一条短信：\"别查了，为了你好。——陈远志的妻子\"",
            "",
            "陈远志有妻子？档案上写的是\u201C离异\u201D。林夜立刻打电话给陈远志生前的同事。对方支支吾吾了半天，最后甩了一句：\"他前妻三年前就出国了，没人知道去了哪。\"",
            "",
            "那这条短信是谁发的？",
            "",
            "林夜让司机掉头，直接去了陈远志的住处。门锁完好，屋内整整齐齐，没有任何被打斗的痕迹。但林夜在卧室的床垫下发现了一个牛皮纸信封。",
            "",
            "信封里是一沓照片——全是偷拍的。照片里的人是他自己：在报社门口抽烟、在便利店买咖啡、在深夜的小巷里打电话。最近的一张拍的是昨晚，他在地铁站等车时的背影。",
            "",
            "有人在跟踪他。而且跟了很久。",
            "",
            "林夜把照片装回信封，塞进包里。他走出小区时，注意到对面街角停着一辆黑色的轿车。车窗摇下一条缝，里面隐约能看见一个人举着相机。",
            "",
            "林夜没有回头。他点了一根烟，拐进了最近的地铁站。",
            "",
            "但他没有上车。他站在站台的柱子后面，盯着入口的方向。大约两分钟后，一个戴棒球帽的男人快步走了进来。他穿着黑色夹克，手里攥着一个对讲机。",
            "",
            "男人扫了一眼站台，没有找到林夜，压低声音对着对讲机说了句什么。然后转身快步离开了。",
            "",
            "林夜从柱子后面走出来，掐灭了烟头。他掏出手机，给那个陌生号码回了一条短信：\"我们见一面。\"",
            "",
            "不到十秒，对方回了两个字：",
            "",
            "\"今晚。\""
        ].join("\n");

        loadSampleBtn.addEventListener("click", () => {
            novelText.value = SAMPLE_NOVEL;
            // 同时填上作品名称
            const titleInput = document.getElementById("title");
            if (titleInput) titleInput.value = "迷雾追踪";
            // 更新章节统计
            if (typeof updateChapterCount === "function") updateChapterCount();
            showToast("✅ 已加载示例小说《迷雾追踪》", "success");
        });
    }
});
