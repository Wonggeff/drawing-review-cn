# 更新日志

本文件记录本技能的重要变更。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.1.1] - 2025-09

**脱敏修复版。** 1.1.0 发布后做了一次全量敏感信息复查，发现并在全部文件中清除了项目专有信息残留。

### 修复（重要）

- **删除 `scripts/dupfind.py`**：该脚本内含一份针对原项目写死的图纸路径字典（大量真实图号与单体编号）。
  其功能已完全被 `pixdiff.py --all`（缓存 + 两级筛选 + 批量报表）覆盖，故直接下线。
- `scripts/merge_findings.py` / `scripts/make03.py`：分册显示名从“原项目单体名”改为通用默认值
  （建筑·分册一/二/三…），新增配置键 `cluster_names` 供使用者映射为自己的单体名。
- `scripts/ledger.py`：专业识别从“匹配某审查平台的文件夹前缀”改为
  **按目录名中的通用专业关键词匹配**（建筑/结构/给排水/电气/暖通/景观/装修/基坑/节能/智能化/海绵），
  且只在目录名中匹配以避免被文件名误判；新增配置键 `discipline_rules` 可覆盖。
- `scripts/dupscan.py` / `scripts/pixdiff.py` / `scripts/dump.scr`：移除硬编码的本地工作路径与项目分册名。
- 文档与案例：图号示例改为虚构编号；规模数据粗化；博客文件名去掉具体数字。
- `.gitignore` 新增 `sensitive.txt`。
  > 注意：`.gitignore` **不支持行尾注释**。原先写成 `sensitive.txt   # 说明` 会让整行（含注释文字）被当成匹配模式，
  > 结果文件实际**没有**被忽略。已改为注释单独成行，并补上 `sensitive-*.txt`、`config.local.json`。
- `scripts/common.py`：修复配置文件里的**自定义扩展键被丢弃**的问题。原先 `_load()` 只保留 `SPEC` 中登记过的键，
  导致 `cluster_names` / `discipline_rules` / `sensitive_patterns` 三项即使写进 `config.json` 也不生效
  （脚本通过 `cfg._v` 读取，永远拿到 `None`）。现在除 `_` 开头的注释键外全部保留，
  并在 `python common.py` 输出中单列“扩展键（自定义）”。

### 新增

- **`scripts/prescan.py`：发布前自检工具**。扫描仓库是否残留项目名、单位、地点、设计号、图号、单体名。
  **脚本本身不硬编码任何项目名**，敏感词来源三选一：命令行参数、仓库根 `sensitive.txt`（已 gitignore）、
  `config.json` 的 `sensitive_patterns`。命中时退出码为 1，可挂到 pre-commit / pre-push。
- `sensitive.example.txt`：敏感词清单模板，按“项目名称／参与单位／地点／设计号／单体名称／本地路径”分类。
  其中**单体名称**最容易遗漏，建议逐个列出。
- `config.example.json` 补充 `cluster_names`、`discipline_rules`、`sensitive_patterns` 三个可选键。

> **发布流程提醒**：`prescan.py` 早期版本把自己放进了跳过名单，结果它自己文档字符串里的一行用法示例
> （真实项目名）反而查不出来 —— 已改为**自我扫描**。同理，改完工作区不等于改完仓库：
> 被删除的敏感文件仍留在旧提交里，`git push --force` 之后旧提交依然能按 SHA 匿名读取。
> 如果确实推过含真实项目信息的提交，仅靠强推不足以清除，需要删除并重建仓库（或联系 GitHub 支持）。
> 本仓库即因此重建过一次。发布前请用 `git grep` 扫**全部历史**，而不只是当前工作区。

## [1.1.0] - 2025-09

### 新增

- **英文 README** `README.en.md`；中文 README 增加语言切换与技术文章入口
- **技术文章** `docs/blog/01-施工图会审自动化实践.md`（含 Mermaid 流程图、对撞示意表与配图）
- `docs/blog/images/` 配图（由脚本生成的示意图，不含任何真实项目数据）
- `pixdiff.py` 批量报表输出：`--report <md>` 与 `--csv <csv>`

### 改进

- **`pixdiff.py` 性能重写**
  - numpy 向量化差异计算（无 numpy 时自动退化为纯 Python）
  - 页面位图**只渲染一次并缓存**：批量模式把 O(N²) 次渲染降为 O(N) 次
  - **两级筛选**：先比 64×64 缩略图（`--thumb-tol` 可调，默认 10），明显不同的直接跳过
  - 渲染阶段支持多线程并行（`--jobs`）
  - 实测（数十张图纸 / 数千对）：无筛选 98.9s → 启用预筛 **56.6s**（跳过约 68% 的图对），
    **结果完全一致，无漏检**
  - 修正：差异百分比由“隔行隔列采样估算”改为**全像素精确值**，
    同一对图纸的读数会与 1.0.0 略有差异（新值更准确）
- `requirements.txt` 增加可选的 `numpy`（建议安装）
- `references/04` 与 `SKILL.md` 的脚本清单同步更新
- 新增 `docs/blog/` 配图生成脚本 `make_figs.py`（示意图，不含真实项目数据）

## [1.0.0] - 2025-09

首个公开版本。内容来自一次完整实战项目（城市建成区文旅项目，千余张唯一施工图 / 二百余个 DWG）的沉淀。

### 新增

- `SKILL.md` 技能主文件：核心原则、七步流程、A/B/C/D 分类口径、9 列输出格式、交付物清单、
  跨专业必查十项、脚本索引、边界与免责
- `references/01-审查流程与交付物.md`：逐步执行要点、子代理派发策略与提示词要素、
  合并出件命令、会审会议组织建议（按“问题包”分议题）
- `references/02-各专业审查要点.md`：11 个专业/专项检查清单
  （总图 / 建筑 / 结构 / 给排水含海绵 / 电气含防雷亮化 / 暖通 / 智能化 / 装修 / 景观 / 基坑 /
  仿古木结构文物专项），设计为可直接粘贴进子代理提示词
- `references/03-跨专业碰撞与常见缺陷模式.md`：20 项跨专业对撞表 + 6 类缺陷模式库
  （标高类 / 图纸集组织类 / 跨专业对撞类 / 规范签章类 / 危大安全类 / 深度不足类）+ 优先级判定标准
- `references/04-图纸取证方法与工具.md`：中国施工图 PDF“读不了”的三种情形与对策、
  DWG 全量文字提取完整方案（含 6 个常见坑）、图像识读策略、像素级比对、坐标窗口重建表格
- `references/05-问题清单与记录表模板.md`：子代理输出模板、主件结构模板、
  Word/Excel 记录表结构、会审纪要写法要点
- `scripts/`：24 个可用脚本
  - 统一配置：`common.py`（配置文件 + 环境变量 + 内置默认三级优先级）
  - 台账与探测：`ledger.py`、`extract_pdf.py`、`probe.py`、`summarise.py`
  - 渲染与读图：`render_all.py`、`render_ext.py`、`findpng.py`、`crop.py`、`rendered.py`
  - DWG 文字提取：`batch_dump2.ps1`、`dump.lsp`、`dump.scr`
  - DWG 文字检索：`gw.py`、`near.py`、`table.py`、`subitems.py`、`dump1.py`、`grepdwg.py`
  - 重复与比对：`dupscan.py`（MD5）、`pixdiff.py`（像素级套用检测）
  - 文档提取：`read_docx.py`
  - 合并与出件：`merge_findings.py`、`make03.py`、`make_docs.py`
- `CASE.md`：脱敏实战案例与自我更正记录
- `config.example.json`、`requirements.txt`、`LICENSE`(MIT)、`.gitignore`、`CONTRIBUTING.md`

### 已知局限

- 规范条文时效性不保证，脚本不内置条文库
- 扫描件（无文字层）只能靠读图，无法逐条核对时需明确写出证据边界
- DWG 全量文字提取依赖本机已安装 AutoCAD
- 暖通冷负荷计算书逐房间明细、智能化系统图逐点核对等细颗粒度工作未自动化

### 计划中

- [ ] 规范条文索引（按专业整理常用强条编号，标注现行版本与核对日期）
- [ ] 支持 Excel 版问题清单直接录入（跳过 Markdown 中间格式）
- [ ] `pixdiff.py` 支持跨专业图签区批量比对报表
- [ ] 英文界面与国际项目（英标/ASTM）要点
