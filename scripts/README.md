# scripts 使用说明

所有脚本共用 `common.py` 的路径配置。**不需要再修改脚本源码里的路径。**

## 一、首次配置

```bash
python common.py --init      # 在本目录生成 config.json
python common.py --init --here   # 或在当前工作目录生成
python common.py             # 查看当前生效配置与解析后的绝对路径
```

`config.json` 关键项：

| 键 | 说明 |
|---|---|
| `drawing_root` | **施工图根目录**（内含各专业分册子目录；PDF/DWG 都放这里） |
| `dup_subdir` | 需跳过的重复归档子目录名（相对 `drawing_root`），无则留空 |
| `render_dir` / `extract_dir` / `dwgtext_dir` | 渲染 PNG / PDF 文字 / DWG 文字的输出目录 |
| `findings_dir` | 各专业分册问题报告目录（`merge_findings.py` 从这里读） |
| `out_dir` | 交付物输出目录（清单、记录表） |
| `main_issue_md` | 主件问题清单文件名（`make_docs.py` 用它生成记录表） |
| `project_name` / `project_location` / `client` / `designer` / `surveyor` / `reviewer` | 写入 Word/Excel 会审记录表的工程信息 |

**可选配置键**（用于适配不同项目）：`cluster_names`（分册代号→单体名）、`discipline_rules`（目录名关键词→专业名）、`sensitive_patterns`（发布前自检敏感词）、`project_name`/`client`/`designer` 等工程信息。

**也可用环境变量覆盖**（优先级高于配置文件）：
`DRAWING_REVIEW_ROOT`、`DRAWING_REVIEW_RENDER`、`DRAWING_REVIEW_DWGTEXT`、
`DRAWING_REVIEW_FINDINGS`、`DRAWING_REVIEW_OUT`、`DRAWING_REVIEW_CONFIG` 等
（完整列表见 `common.py` 的 `SPEC`）。

**查找顺序**：环境变量 → `DRAWING_REVIEW_CONFIG` 指定的文件 → `./config.json` → 本目录 `config.json` → 内置默认。

## 二、依赖

```bash
python -m pip install -r ../requirements.txt
# 即 pymupdf openpyxl python-docx
```

- `pymupdf`：PDF 渲染、文字提取、图像裁剪
- `openpyxl`：生成 Excel 会审记录表
- `python-docx`：生成 Word 会审记录表
- **DWG 文字提取额外需要**：AutoCAD（含 `accoreconsole.exe`）与 PowerShell 7
  - `accoreconsole.exe` 路径可用 `DRAWING_REVIEW_ACCORECONSOLE` 指定
- 注意：不要把 `read_docx.py` 改名为 `docx.py`，否则会遮蔽 `python-docx` 包

## 三、典型执行顺序

```bash
# 1) 台账（不需读图即可发现一批问题）
python ledger.py

# 2) PDF 文字层探测（判断哪些图只能读图）+ 抽样了解构成
python extract_pdf.py
python probe.py

# 3) DWG 全量文字提取（可后台跑；需 AutoCAD）
pwsh -File batch_dump2.ps1

# 4) 图纸渲染
python render_all.py

# 5) 定位与放大（分析阶段反复使用）
python findpng.py "结构分册" 300
python crop.py "<某基础图>" 0.33 0.75 0.62 0.88 out.png 6

# 6) 跨图纸关键词检索（跨专业比对的主力）
python gw.py "抗浮" 6 ""
python gw.py "±0.000(" 6 "01-建筑"
python gw.py "相当于绝对标高" 6 ""

# 7) 像素级比对（查“张冠李戴 / 图纸套用”）
python pixdiff.py "某分册\X-01" "某分册\Y-01"
python pixdiff.py --all "某分册" --min-sim 97 --report r.md --csv r.csv

# 8) 合并子代理产出并出交付物
python merge_findings.py
python make03.py
python make_docs.py
```

## 四、脚本清单

| 脚本 | 用途 |
|---|---|
| `common.py` | **统一路径与工程信息配置**（公共依赖，可 `--init` / `--show`） |
| `ledger.py` | 从文件路径生成图纸台账，统计分册张数、识别重名/重号/缺号 |
| `extract_pdf.py` | 提取全部 PDF 文字层，输出每张图的可提取字符数 |
| `probe.py` | 抽样探测单张 PDF 的文字层与图元构成 |
| `summarise.py` | 汇总各分册的文字层覆盖情况 |
| `render_all.py` | 批量渲染唯一 PDF 为 PNG（自动跳过嵌套重复目录） |
| `render_ext.py` | 渲染图纸目录之外的 PDF（变更单、地勘附图、项目资料） |
| `findpng.py` | 按路径片段定位图纸的渲染 PNG |
| `rendered.py` | 查看渲染覆盖情况 |
| `crop.py` | 按页面比例裁剪并高倍放大（读表格、尺寸链、图号栏、印章） |
| `batch_dump2.ps1` + `dump.lsp` + `dump.scr` | **AutoCAD Core Console 批量提取全部 DWG 文字（并行 5 路）** |
| `gw.py` | 在全部 DWG 文字中按关键词检索并反查来源图纸 |
| `near.py` | 按坐标窗口提取 DWG 文字（重建表格） |
| `table.py` | 重建 DWG 表格区域（按 y 降序、x 升序） |
| `subitems.py` | 从设计总说明 DWG 中提取“子项概况”表 |
| `dump1.py` / `grepdwg.py` | 单文件导出 / 跨文件检索（GBK） |
| `dupscan.py` | MD5 比对：找出重复归档且内容一致的文件 |
| `pixdiff.py` | **指定两张图做像素比对**，判定“同一张图 / 大幅套用 / 不同图” |
| `read_docx.py` | 提取 .docx 全文（地勘报告、设计说明等） |
| `merge_findings.py` | 合并各分册问题为统一编号清单（MD + CSV）并统计 |
| `make03.py` | 生成“各专业问题明细清单” |
| `make_docs.py` | 生成 Word/Excel 会审记录表（含设计回复/处理结果/闭环状态列与签认栏） |
| `prescan.py` | **发布前自检**：扫描仓库是否残留项目名/单位/地点/图号（敏感词来自 `sensitive.txt`，脚本不硬编码） |

## 五、常见问题

| 现象 | 原因与处理 |
|---|---|
| 脚本报 `NO MATCH` / `命中不足` | `drawing_root` 配错，或路径片段写错。用 `python gw.py` 先确认文件确实存在 |
| PDF 抽取出的文字是乱码（如 `ᔔㆇᇼᓜ`） | 字体缺 ToUnicode 映射，无法恢复。改用渲染读图 |
| 图片读取失败（单边超 8192px） | 先 `crop.py` 分块再读 |
| `pwsh -File batch_dump2.ps1` 报 `no function definition: DUMPTEXT` | `SECURELOAD` 未置 0；脚本首行已处理，若手动改过请恢复 |
| DWG 提取报 `stringp 1` | `(getvar "DWGTITLED")` 返回整数，需 `itoa` 包装 |
| 中文输出乱码 | 脚本已 `reconfigure(encoding="utf-8")`；若仍乱码请用支持 UTF-8 的终端 |
