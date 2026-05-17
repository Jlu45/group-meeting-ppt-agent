<div align="center">

# 🎓 Group Meeting PPT Agent

### 组会PPT自动制作智能体

**From any document to a polished, template-compliant PPTX — no LLM API required**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg)](CONTRIBUTING.md)

[English](#-features) · [中文](#-核心特性)

</div>

***

## ✨ Features

| Feature | Description |
| ------- | ----------- |
| 🧬 **Template DNA Extraction** | OOXML deep parsing of master / layout / placeholder / decoration — full design spec in one pass |
| 📐 **Layout-Driven Rendering** | Zero hardcoded coordinates; content binds to template placeholders via semantic matching |
| 🏗️ **Semantic Asset Layer** | Structured intermediate representation: ContentUnit / Evidence / TableAsset / FigureAsset / CodeAsset / MetricAsset |
| 🔍 **Smart File Recognition** | 40+ extensions, 20 naming patterns — auto-detect file type, PPT purpose, and sequence |
| 🤖 **AI 编程助手 Native** | SKILL.md + pure tool scripts + JSON contracts — works with Claude Code / Trae / Cursor, no LLM API calls |
| 🛡️ **4-Level Validation + Auto-Repair** | Structure → Layout → Compliance → Content, with up to 3 automatic repair rounds |
| 📊 **Density Control** | Auto split dense slides, compress verbose bullets, merge sparse slides |

***

## ✨ 核心特性

| 特性 | 说明 |
| ---- | ---- |
| 🧬 **模板DNA提取** | OOXML深度解析母版/版式/占位符/装饰元素，一次提取完整设计规范 |
| 📐 **布局驱动渲染** | 零硬编码坐标，内容通过语义匹配绑定到模板占位符 |
| 🏗️ **语义资产层** | 结构化中间表示：ContentUnit / Evidence / TableAsset / FigureAsset / CodeAsset / MetricAsset |
| 🔍 **智能文件识别** | 40+扩展名、20命名模式——自动检测文件类型、PPT用途和序号 |
| 🤖 **AI IDE原生集成** | SKILL.md + 纯工具脚本 + JSON契约——适配Claude Code / Trae / Cursor，无需LLM API调用 |
| 🛡️ **四级验证 + 自动修复** | 结构 → 布局 → 合规 → 内容，最多3轮自动修复 |
| 📊 **密度控制** | 自动拆分过密幻灯片、压缩冗长要点、合并稀疏页面 |

***

## 🏗️ Architecture / 技术架构

### Eight-Layer Architecture / 八层架构

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           System Architecture                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ 1. Input Layer / 输入层                                            │  │
│  │    PDF / DOCX / MD / TXT / PNG / XLSX / PY / BIB + Template PPTX  │  │
│  └──────────────────────────────┬─────────────────────────────────────┘  │
│                                 ↓                                        │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ 2. File Recognition Layer / 文件识别层                              │  │
│  │    SmartFileRecognizer: 40+ exts, 20 naming patterns               │  │
│  │    → FileRecognitionResult (type, purpose, sequence, confidence)   │  │
│  └──────────────────────────────┬─────────────────────────────────────┘  │
│                                 ↓                                        │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ 3. Parsing Layer / 解析层                                          │  │
│  │    UniversalDocumentParser (MarkItDown / Docling) → Markdown       │  │
│  └──────────────────────────────┬─────────────────────────────────────┘  │
│                                 ↓                                        │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ 4. Semantic Asset Layer / 语义资产层                                │  │
│  │    AssetBuilder → AssetStore                                       │  │
│  │    ContentUnit · Evidence · TableAsset · FigureAsset               │  │
│  │    CodeAsset · MetricAsset                                         │  │
│  └──────────────────────────────┬─────────────────────────────────────┘  │
│                                 ↓                                        │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ 5. Planning Layer / 规划层                                         │  │
│  │    Planner (rule-based) → SlideSpec[]                              │  │
│  │    DensityController: auto split / compress / merge                │  │
│  └──────────────────────────────┬─────────────────────────────────────┘  │
│                                 ↓                                        │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ 6. Template Layout Layer / 模板布局层                               │  │
│  │    OOXMLTemplateParser → TemplateDNA                               │  │
│  │    LayoutClassifier · LayoutMatcher · PlaceholderBinder            │  │
│  └──────────────────────────────┬─────────────────────────────────────┘  │
│                                 ↓                                        │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ 7. Rendering Layer / 渲染层                                        │  │
│  │    LayoutDrivenRenderer: layout-driven, zero hardcoded coords      │  │
│  │    python-pptx + matplotlib + Style Lock                           │  │
│  └──────────────────────────────┬─────────────────────────────────────┘  │
│                                 ↓                                        │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ 8. Validation & Repair Layer / 验证与修复层                         │  │
│  │    VisualValidator (4 levels) → QualityReporter (A/B/C/D)          │  │
│  │    Auto-fix up to 3 rounds                                         │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Pipeline Flow / 流水线流程

```
Input Layer → File Recognition Layer → Parsing Layer → Semantic Asset Layer
    → Planning Layer → Template Layout Layer → Rendering Layer
    → Validation & Repair Layer → PPTX + Quality Report
```

***

## 🚀 Quick Start / 快速开始

### Prerequisites / 前置条件

- Python 3.10+
- pip

### Installation / 安装

```bash
git clone https://github.com/YOUR_USERNAME/group-meeting-ppt-agent.git
cd group-meeting-ppt-agent
pip install -r requirements.txt
```

### Basic Usage / 基本用法

```bash
python -m src.agent experiment.md -t lab_template.pptx -a "张三"
```

***

## 📖 CLI Usage / 命令行用法

### Main Command / 主命令

```bash
python -m src.agent <files> -t <template> -a <author>

# Examples / 示例
python -m src.agent paper.pdf -t lab_template.pptx -a "张三"
python -m src.agent experiment.md data.xlsx fig.png -t template.pptx -a "Li Ming"
python -m src.agent notes.md --outline-only -a "王五"
```

| Parameter | Description | Default |
| --------- | ----------- | ------- |
| `input_files` | Input file paths (positional, required) | - |
| `-t, --template` | Template PPTX path | None |
| `-a, --author` | Presenter name | "" |
| `-d, --date` | Date string | auto |
| `-o, --output-dir` | Output directory | `./output` |
| `--outline-only` | Only print outline, don't generate PPTX | False |

### Individual Tool Scripts / 独立工具脚本

Each step can be invoked independently via JSON contracts / 每一步均可通过JSON契约独立调用：

```bash
# Step 1: Recognize file types / 文件识别
python -m src.tools.recognize_files paper.pdf data.xlsx --output recognition.json

# Step 2: Parse documents / 文档解析
python -m src.tools.parse_documents paper.pdf --output parsed.json

# Step 3: Extract template DNA / 模板DNA提取
python -m src.tools.extract_template_dna lab_template.pptx --output template_dna.json

# Step 4: Build asset store / 构建资产库
python -m src.tools.build_asset_store --recognition recognition.json --parsed parsed.json --output asset_store.json

# Step 5: Render PPTX / 渲染PPTX
python -m src.tools.render_pptx --slide-specs slide_specs.json --template-dna template_dna.json --output result.pptx

# Step 6: Validate PPTX / 验证PPTX
python -m src.tools.validate_pptx result.pptx --template-dna template_dna.json --output report.json

# Step 7: Repair PPTX / 修复PPTX
python -m src.tools.repair_pptx --pptx result.pptx --issues report.json --output repaired.pptx
```

***

## 🤖 AI IDE Integration / AI IDE集成

The project ships with `skills/group-meeting-ppt-agent/SKILL.md` — a declarative skill definition that tells AI IDEs (Claude Code, Trae, Cursor) how to orchestrate the pipeline.

项目自带 `skills/group-meeting-ppt-agent/SKILL.md`——声明式技能定义，指导AI IDE编排流水线。

### How it works / 工作原理

1. AI IDE reads `SKILL.md` to understand the pipeline and constraints
2. AI IDE calls **pure tool scripts** (no LLM API calls inside) via CLI
3. Data flows between steps via **JSON contracts** (`schemas/*.schema.json`)
4. AI IDE handles high-level decisions (planning, refinement) while tools handle deterministic work

### Key constraints / 核心约束

- Tool scripts **never** call OpenAI / Anthropic API
- No hardcoded PPT coordinates unless template has no usable layout
- Must call validation tool after rendering
- Auto-repair up to 3 rounds on failure

### Usage with Claude Code / Trae / Cursor

```
# In your AI IDE, point to the skill:
/skills/group-meeting-ppt-agent

# Then ask:
"用 lab_template.pptx 把 experiment.md 做成组会PPT"
```

***

## 📁 Project Structure / 项目结构

```
group-meeting-ppt-agent/
├── README.md
├── requirements.txt
├── setup.py
├── LICENSE
│
├── schemas/                          # JSON Schema contracts / JSON契约
│   ├── asset_store.schema.json
│   ├── file_recognition.schema.json
│   ├── render_log.schema.json
│   ├── shared_state.schema.json
│   ├── slide_spec.schema.json
│   ├── slide_specs.schema.json
│   ├── template_dna.schema.json
│   └── validation_report.schema.json
│
├── skills/                           # AI IDE skill definitions / AI IDE技能定义
│   └── group-meeting-ppt-agent/
│       ├── SKILL.md                  # Skill manifest / 技能清单
│       ├── constraints.md            # Constraints / 约束
│       ├── prompts/
│       │   ├── planning_prompt.md
│       │   └── refinement_prompt.md
│       └── examples/
│           ├── experiment_log_to_ppt.md
│           ├── literature_note_to_ppt.md
│           └── progress_report_to_ppt.md
│
├── src/
│   ├── __init__.py
│   ├── agent.py                      # Main entry (8-step pipeline) / 主入口
│   ├── models.py                     # Legacy models (compat) / 旧模型(兼容)
│   │
│   ├── common/                       # Shared models & utilities / 共享模型与工具
│   │   ├── __init__.py
│   │   ├── models.py                 # All data classes / 全部数据类
│   │   └── json_io.py               # JSON read/write helpers / JSON读写
│   │
│   ├── recognition/                  # Layer 2: File Recognition / 文件识别层
│   │   ├── __init__.py
│   │   └── file_recognizer.py       # SmartFileRecognizer
│   │
│   ├── parsers/                      # Layer 3: Document Parsing / 文档解析层
│   │   ├── __init__.py
│   │   ├── document_parser.py       # UniversalDocumentParser
│   │   ├── template_extractor.py    # Template DNA extractor (legacy)
│   │   └── content_structurer.py    # Content structurer (legacy)
│   │
│   ├── assets/                       # Layer 4: Semantic Asset / 语义资产层
│   │   ├── __init__.py
│   │   └── asset_builder.py         # AssetBuilder → AssetStore
│   │
│   ├── planning/                     # Layer 5: Planning / 规划层
│   │   ├── __init__.py
│   │   └── density_controller.py    # DensityController (split/compress/merge)
│   │
│   ├── template/                     # Layer 6: Template Layout / 模板布局层
│   │   ├── __init__.py
│   │   ├── ooxml_parser.py          # OOXMLTemplateParser → TemplateDNA
│   │   └── layout_classifier.py     # classify_layout()
│   │
│   ├── rendering/                    # Layer 7: Rendering / 渲染层
│   │   ├── __init__.py
│   │   ├── pptx_renderer.py         # LayoutDrivenRenderer
│   │   ├── layout_matcher.py        # LayoutMatcher
│   │   └── placeholder_binder.py    # PlaceholderBinder
│   │
│   ├── validation/                   # Layer 8: Validation & Repair / 验证与修复层
│   │   ├── __init__.py
│   │   ├── visual_validator.py      # VisualValidator (4-level)
│   │   └── quality_reporter.py      # QualityReporter (A/B/C/D grade)
│   │
│   ├── tools/                        # CLI tool scripts / 独立工具脚本
│   │   ├── __init__.py
│   │   ├── recognize_files.py
│   │   ├── parse_documents.py
│   │   ├── extract_template_dna.py
│   │   ├── build_asset_store.py
│   │   ├── render_pptx.py
│   │   ├── validate_pptx.py
│   │   └── repair_pptx.py
│   │
│   ├── agents/                       # Agent modules (legacy) / 智能体模块(兼容)
│   ├── generators/                   # Generator modules (legacy) / 生成模块(兼容)
│   ├── validators/                   # Validator modules (legacy) / 验证模块(兼容)
│   └── templates/
│       ├── create_template.py
│       └── default_academic.pptx
│
└── tests/
    └── test_all.py
```

***

## 📋 JSON Contracts / JSON契约

All inter-layer data is governed by JSON Schema files in `schemas/`:

所有层间数据均由 `schemas/` 中的JSON Schema约束：

| Schema | Description | 说明 |
| ------ | ----------- | ---- |
| `file_recognition.schema.json` | File recognition results | 文件识别结果 |
| `asset_store.schema.json` | Semantic asset store | 语义资产库 |
| `template_dna.schema.json` | Template DNA specification | 模板DNA规范 |
| `slide_spec.schema.json` | Single slide specification | 单页幻灯片规范 |
| `slide_specs.schema.json` | Slide specification collection | 幻灯片规范集合 |
| `shared_state.schema.json` | Pipeline shared state | 流水线共享状态 |
| `render_log.schema.json` | Rendering log | 渲染日志 |
| `validation_report.schema.json` | Validation & quality report | 验证与质量报告 |

***

## 📊 Quality Report / 质量报告

Example output / 输出示例：

```json
{
  "structure_score": 100,
  "layout_score": 85,
  "compliance_score": 92,
  "content_score": 95,
  "overall_score": 92.4,
  "grade": "A",
  "slide_count": 12,
  "issue_summary": {
    "total": 3,
    "by_severity": { "warning": 2, "info": 1 },
    "by_level": { "layout": 2, "compliance": 1 },
    "by_type": { "font_mismatch": 1, "margin_violation": 2 }
  }
}
```

### Grade Scale / 评分等级

| Grade | Score Range | Meaning |
| ----- | ----------- | ------- |
| **A** | ≥ 85 | Excellent — ready to present / 优秀——可直接使用 |
| **B** | 70 – 84 | Good — minor issues / 良好——有小问题 |
| **C** | 60 – 69 | Acceptable — needs review / 及格——需检查 |
| **D** | < 60 | Poor — requires rework / 不及格——需返工 |

### 4-Level Validation / 四级验证

| Level | Validation | Pass Condition |
| ----- | ---------- | -------------- |
| Structure | Blank slides, missing titles, slide count | Issues = 0 |
| Layout | Overflow, overlap, margin violation, font size | No critical/error |
| Compliance | Font mismatch, color mismatch vs template DNA | Score ≥ 90% |
| Content | Placeholder text, incomplete content | No P0 issues |

***

## 🙏 Acknowledgments / 致谢

| Project | Contribution |
| ------- | ------------ |
| [ppt-master](https://github.com/hugohe3/ppt-master) | Template DNA extraction, SVG→native PPTX |
| [MarkItDown](https://github.com/microsoft/markitdown) | Universal document → Markdown conversion |
| [Docling](https://github.com/docling-project/docling) | Complex PDF deep parsing |
| [Auto-Slides](https://github.com/Westlake-AGI-Lab/Auto-Slides) | Multi-agent collaboration pattern |
| [pptx-generator](https://github.com/paul0728/pptx-generator) | Slide type schema design |

***

## 📄 License / 许可证

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

本项目基于 MIT 许可证开源，详见 [LICENSE](LICENSE) 文件。

***

<div align="center">

**Made with ❤️ for researchers who hate making PPTs**

**用 ❤️ 为讨厌做PPT的科研人打造**

</div>
