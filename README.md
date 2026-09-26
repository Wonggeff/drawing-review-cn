# drawing-review-cn · 图纸会审（施工图自审）智能体技能

> 面向中国建筑工程的**施工图图纸会审**作业包：一套可执行的流程 + 工具链 + 检查清单 + 交付物模板。
> 输入一个装满施工图的文件夹（PDF/DWG），输出**可直接上会签认**的图纸会审问题清单与记录表。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Language](https://img.shields.io/badge/lang-中文-blue)

> English version: [README.en.md](README.en.md)
>
> 📖 技术文章：[一次施工图会审的自动化实践：从千余张图纸到 703 条问题](docs/blog/01-施工图会审自动化实践.md)

---

## 这是什么

一个 Agent Skill（适用于 Claude Code / OpenCodex / DeepSeek Harness 等支持 `SKILL.md` 的智能体框架），
把"图纸会审"这件事从**靠个人经验翻图**变成**可复现的工程化流程**：

- **怎么读图**：中国施工图 PDF 常常没有可用文字层（CAD 出图缺 ToUnicode，抽取为乱码），
  本技能给出替代取证方案——**DWG 全量文字提取 + 高分辨率渲染图像识读**。
- **查什么**：11 个专业/专项的审查要点清单（可直接作为子代理提示词）+ 20 项跨专业对撞表 + 6 类缺陷模式库。
- **怎么组织**：七步流程（台账 → 取证 → 基础图通读 → 专业并行 → 跨专业核查 → 合并分级 → 出件）。
- **出什么**：问题清单（主件）、专业明细、Word/Excel 会审记录表（含设计回复/处理结果/闭环状态列与四方签认栏）。

## 快速开始

```bash
git clone https://github.com/Wonggeff/drawing-review-cn.git
cd drawing-review-cn

# 1) 安装依赖
python -m pip install -r requirements.txt

# 2) 生成配置并填写你的项目路径
python scripts/common.py --init
#   编辑 config.json：drawing_root 指向施工图根目录；out_dir 指向交付物输出目录

# 3) 建取证能力
python scripts/ledger.py                 # 图纸台账 + 编号异常
python scripts/extract_pdf.py            # 判断哪些图纸无文字层
pwsh -File scripts/batch_dump2.ps1       # DWG 全量文字（需 AutoCAD，可跳过）
python scripts/render_all.py             # 渲染为 PNG（供图像识读）

# 4) 分析
python scripts/gw.py "±0.000(" 6 "01-建筑"      # 跨图纸关键词检索
python scripts/pixdiff.py "<图A片段>" "<图B片段>"  # 像素级比对（查张冠李戴）

# 5) 出件（在 _findings/ 里放好各分册报告后）
python scripts/merge_findings.py
python scripts/make03.py
python scripts/make_docs.py
```

把本仓库（或其父目录）作为技能目录，即可在智能体里用自然语言触发：
> "帮我做图纸会审"、"图纸自审"、"审图"、"挑图纸问题"、"出问题清单"、"会审记录"

## 目录结构

```
drawing-review-cn/
├── SKILL.md                              # 技能主文件（原则 / 七步流程 / 分类口径 / 脚本索引）
├── references/
│   ├── 01-审查流程与交付物.md              # 逐步执行要点、子代理派发、会议组织
│   ├── 02-各专业审查要点.md                # 11 个专业/专项检查清单（可直接粘贴进提示词）
│   ├── 03-跨专业碰撞与常见缺陷模式.md       # 20 项对撞表 + 6 类缺陷模式库 + 优先级判定
│   ├── 04-图纸取证方法与工具.md            # PDF 读不了时的替代方案、DWG 提取、像素比对
│   └── 05-问题清单与记录表模板.md          # 输出格式与模板
├── scripts/                              # 24 个可用脚本（统一由 common.py 配置路径）
├── config.example.json
├── CASE.md                               # 实战案例（脱敏）
├── CHANGELOG.md
└── CONTRIBUTING.md
```

## 核心能力

| 能力 | 脚本 | 说明 |
|---|---|---|
| 图纸台账与编号异常 | `ledger.py` | 分册张数、同名重复、图号重号缺号 |
| **DWG 全量文字提取** | `batch_dump2.ps1` + `dump.lsp` | AutoCAD Core Console 并行 5 路，二百余个 DWG 约 30 分钟 |
| **跨图纸关键词检索** | `gw.py` | 对全项目 CAD 做精确检索，是跨专业比对的主力 |
| 表格重建 | `near.py` / `table.py` / `subitems.py` | 按坐标窗口还原 DWG 表格 |
| 高分辨率渲染与放大 | `render_all.py` / `crop.py` | 读图、读表格、读印章 |
| **像素级比对** | `pixdiff.py` | 判定"同一张图 / 大幅套用 / 不同图"，客观可复核 |
| MD5 重复归档比对 | `dupscan.py` | 明确"以哪一份为准" |
| 地勘/说明全文提取 | `read_docx.py` | docx 全文，便于参数核校 |
| 合并与出件 | `merge_findings.py` / `make03.py` / `make_docs.py` | 统一编号清单 + Word/Excel 会审记录表 |
| **发布前自检** | `prescan.py` | 扫描仓库是否残留项目名／单位／地点／图号（敏感词来自 `sensitive.txt`） |

## 问题分类口径

| 类别 | 含义 | 处理方式 |
|---|---|---|
| **A 设计错误** | 违反强制性条文、计算错误、明显设计错误 | 设计出变更图；涉及强制性标准的须重新报审 |
| **B 图纸矛盾** | 平立剖不一致、图与表不符、专业间矛盾、版本冲突 | 设计书面确认 |
| **C 深度不足** | 节点不清、尺寸/做法缺失、说明空白、无法指导施工 | 设计补充说明或详图 |
| **D 施工建议** | 可优化的施工方案 | 设计确认后执行 |

严重程度：**高**（结构/消防/文物安全、功能、造价、工期）／**中**（施工组织或需澄清）／**低**（表达瑕疵）。

## 交付物（标准四件套）

| 文件 | 内容 |
|---|---|
| `01_图纸会审知识体系与审查要点清单.md` | 制度依据、流程、专业要点、碰撞清单 |
| `02_图纸会审问题清单.md` | **主件**：审查结论与三级优先级、一级问题、跨专业矛盾、图纸集完整性核查、需确认事项 |
| `03_各专业问题明细清单.md` | 全部问题明细（统一编号，9 列） |
| `04_图纸会审记录表.xlsx / .docx` | 上会签认用，含设计回复/处理结果/闭环状态列与四方签认栏 |

## 适用范围与边界

**适用于**：民用建筑与文旅/仿古/木结构项目的施工图自审；
尤其适合**多单体外立面复杂、木结构与混凝土混用、位于历史街区或邻近受保护建筑**的项目。

**不替代**：
- 设计单位的书面答复与设计变更
- 施工图审查机构的复核意见
- 注册结构/建筑师的执业判断
- 危大工程的专家论证

**已知局限**：
- 规范条文的时效性不保证，脚本不内置条文库；不确定的条文请标注"需核对"并自行核实现行版本
- 扫描件（无文字层）只能靠读图，无法逐条核对时应明确写出证据边界
- DWG 文字提取依赖本机已安装 AutoCAD

## 实战验证

本技能在实际项目上运行过一轮完整审查：**千余张唯一施工图 / 二百余个 DWG / 15 个专业分册子代理**，
产出 **703 条问题**（A 设计错误 130、B 图纸矛盾 241、C 深度不足 308、D 施工建议 24），
并归纳出 30 项一级问题与 15 项跨专业矛盾。详见 [CASE.md](CASE.md)。

## 贡献

欢迎补充专业检查清单、新增规范条文、提交脚本改进。见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可

[MIT](LICENSE)
