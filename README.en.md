# drawing-review-cn · Construction Drawing Review Skill (China)

> An **executable workflow + toolchain + checklists + deliverable templates** for China's
> *施工图图纸会审* (construction drawing joint review / pre-construction drawing self-audit).
> Input: a folder full of construction drawings (PDF/DWG).
> Output: a sign-off-ready **issue register** and **review meeting record**.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Language](https://img.shields.io/badge/lang-中文-blue)

> 中文版见 [README.md](README.md)

---

## What this is

An Agent Skill (works with Claude Code / OpenCodex / DeepSeek Harness and any framework that
reads `SKILL.md`). It turns drawing review from *flipping through drawings by gut feeling* into a
**reproducible engineering process**.

- **How to read the drawings** — Chinese construction drawings very often have *no usable text layer*:
  CAD-exported PDFs lack a ToUnicode CMap, so text extraction returns garbage (e.g. `ᔔㆇᇼᓜ`), and many
  sheets are vector outlines or plain scans. This skill ships the workarounds:
  **bulk DWG text extraction via AutoCAD Core Console** + **high-resolution rendering for image reading**.
- **What to look for** — per-discipline checklists for 11 disciplines/specialities, a 20-item
  cross-discipline collision table, and a library of 6 classes of recurring defect patterns.
- **How to organise it** — a 7-step workflow: register → evidence tooling → read the base sheets →
  parallel per-discipline review → project-level & cross-discipline checks → merge & grade → deliverables.
- **What you get** — issue register (main document), per-discipline detail, and a Word/Excel review
  record with columns for designer reply / disposition / closure status and a four-party signature block.

## Why it matters

Single-discipline nitpicking is easy. The expensive mistakes are **cross-discipline**:
a fit-out sheet using a different ±0.000 datum than the structural drawing (max error found: **3.85 m**),
structural slab levels *above* finished floor levels, a fire-compartment numbering scheme that exists in
three incompatible variants, architecture notes claiming a sprinkler system that the plumbing drawings
never detail, or a 165-sheet fit-out package that the design scope statement explicitly excludes.

This skill forces those collisions into the open, with **checkable evidence** for every finding.

## Quick start

```bash
git clone https://github.com/Wonggeff/drawing-review-cn.git
cd drawing-review-cn

# 1) Dependencies
python -m pip install -r requirements.txt

# 2) Create config and point it at your project
python scripts/common.py --init
#   edit config.json: drawing_root -> your drawing folder; out_dir -> deliverables folder

# 3) Build the evidence tooling
python scripts/ledger.py                 # drawing register + numbering anomalies
python scripts/extract_pdf.py            # find out which sheets have no text layer
pwsh -File scripts/batch_dump2.ps1       # bulk DWG text extraction (needs AutoCAD; optional)
python scripts/render_all.py             # render sheets to PNG for image reading

# 4) Analyse
python scripts/gw.py "±0.000(" 6 "01-建筑"        # cross-sheet keyword search
python scripts/pixdiff.py "<sheetA>" "<sheetB>"    # pixel-level comparison (catch copy-paste sheets)
python scripts/pixdiff.py --all "<folder>" --min-sim 97 --report r.md --csv r.csv

# 5) Produce deliverables (after dropping per-discipline reports into _findings/)
python scripts/merge_findings.py
python scripts/make03.py
python scripts/make_docs.py
```

Trigger it in the agent with natural language:
> "帮我做图纸会审" · "图纸自审" · "审图" · "挑图纸问题" · "出问题清单" · "会审记录"
>
> (English prompt: *"Review this construction drawing set and give me a drawing-review issue list
> with discipline, sheet number, location, problem and suggested fix, including cross-discipline checks."*)

## Repository layout

```
drawing-review-cn/
├── SKILL.md                              # core principles / 7-step flow / classification / script index
├── references/
│   ├── 01-workflow-and-deliverables.md   # (zh) step-by-step, sub-agent dispatch, meeting organisation
│   ├── 02-discipline-checklists.md       # (zh) checklists for 11 disciplines — paste into sub-agent prompts
│   ├── 03-cross-discipline-collisions.md # (zh) 20 collision items + 6 defect-pattern classes
│   ├── 04-evidence-toolchain.md          # (zh) what to do when the PDF cannot be read; DWG extraction; pixel diff
│   └── 05-templates.md                   # (zh) issue list & review record templates
├── scripts/                              # 24 scripts, all configured through common.py
├── docs/blog/                            # technical write-up (zh)
├── config.example.json
├── CASE.md                               # anonymised field case
├── CHANGELOG.md / CONTRIBUTING.md / LICENSE
```

> **Note:** `SKILL.md` and `references/` are written in Chinese, because the target artefacts
> (drawing numbers, note wording, code clauses, review-meeting records) are Chinese.
> The scripts and this README are English-friendly.

## Capabilities

| Capability | Script | Notes |
|---|---|---|
| Drawing register & numbering anomalies | `ledger.py` | sheet counts per discipline, duplicate names, duplicated/missing sheet numbers |
| **Bulk DWG text extraction** | `batch_dump2.ps1` + `dump.lsp` | AutoCAD Core Console, 5 parallel workers; 225 DWGs in ~30 min |
| **Cross-sheet keyword search** | `gw.py` | exact search across every DWG in the project — the workhorse for cross-discipline comparison |
| Table reconstruction | `near.py` / `table.py` / `subitems.py` | rebuild DWG tables from scattered TEXT entities by coordinate window |
| High-res render & zoom | `render_all.py` / `crop.py` | read sheets, tables, stamps |
| **Pixel-level comparison** | `pixdiff.py` | decide "same sheet / heavily reused / different"; numpy-vectorised, cached, two-stage filtering, batch reports |
| Duplicate-archive detection | `dupscan.py` | MD5 comparison — establishes which copy governs |
| DOCX full-text extraction | `read_docx.py` | geotechnical reports, design notes |
| Merge & deliver | `merge_findings.py` / `make03.py` / `make_docs.py` | unified numbered register + Word/Excel review record |
| Pre-publish self-check | `prescan.py` | scans the repo for leftover project names / organisations / locations / drawing numbers |

## Issue classification (the vocabulary used throughout)

| Class | Meaning | Handling |
|---|---|---|
| **A — Design error** | violates mandatory clauses, calculation error, evident design mistake | designer issues a change; if mandatory standards involved, re-submit for review |
| **B — Drawing conflict** | plan/elevation/section mismatch, drawing vs schedule mismatch, inter-discipline conflict, version conflict | written confirmation by designer |
| **C — Insufficient detail** | unclear node, missing dimension or specification, blank note, unbuildable | designer supplements notes/detail drawings |
| **D — Constructability advice** | optimisable construction approach | execute after designer confirms |

Severity: **High** (structural / fire / heritage safety, function, cost, schedule — must be closed before
the review meeting) · **Medium** · **Low**.

## Deliverables (standard set of four)

| File | Content |
|---|---|
| `01_*.md` | regulatory basis, workflow, discipline checklists, collision list |
| `02_*.md` | **main document**: conclusion & 3-tier priority, Level-1 issues, cross-discipline conflicts, drawing-set integrity check, items requiring written confirmation |
| `03_*.md` | full issue register (unified numbering, 9 columns) |
| `04_*.xlsx` / `.docx` | review meeting record, with designer-reply / disposition / closure-status columns and a four-party signature block |

## Scope & limitations

**Intended for** architectural and cultural-tourism projects, including timber-structure and
traditional-style (仿古) buildings — especially multi-building sites, mixed timber/concrete systems,
and sites in historic districts or adjacent to protected heritage.

**Does not replace**: the designer's written reply or change notice, the statutory drawing-review
authority's re-check, the professional judgement of registered engineers, or expert panel review of
high-risk work.

**Known limitations**
- Code-clause currency is not guaranteed; the scripts ship no clause database. Mark uncertain clauses
  as "to be verified" and check the current edition yourself.
- Scanned sheets (no text layer) can only be read visually; state the evidence boundary when item-by-item
  verification is impossible.
- Bulk DWG extraction requires AutoCAD installed locally.

## Field validation

One full review run on a real project: **1,000+ unique sheets / 200+ DWGs / 15 discipline sub-agent batches**,
producing **703 findings** (A 130, B 241, C 308, D 24) and 30 Level-1 issues plus 15 cross-discipline
conflicts. See [CASE.md](CASE.md) and the technical write-up in [docs/blog/](docs/blog/).

## Contributing

Improvements to discipline checklists, defect patterns and scripts are welcome —
see [CONTRIBUTING.md](CONTRIBUTING.md). Please never commit real project data.

## License

[MIT](LICENSE)
