<div align="center">

# 🎓 Group Meeting PPT Agent

### 组会PPT自动制作智能体

**From any document to a polished, template-compliant PPTX in minutes**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg)](CONTRIBUTING.md)

[English](#-overview) · [中文](#-概述)

</div>

***

## 🌟 Overview

**Group Meeting PPT Agent** is an intelligent PPT generation tool designed for academic group meeting scenarios. It takes any format of input documents (PDF, Word, Markdown, images, Excel, etc.), strictly follows your lab's PPTX template, and outputs a native, editable PPTX file.

### Key Features

| Feature                           | Description                                                                                      |
| --------------------------------- | ------------------------------------------------------------------------------------------------ |
| 🎨 **Strict Template Compliance** | Template DNA extraction via OOXML deep parsing — colors, fonts, layouts, and decorative elements |
| 📄 **Universal Input**            | Supports PDF/DOCX/Markdown/Text/Images/Excel and mixed formats                                   |
| ✏️ **Native Editable Output**     | Produces real `.pptx` files where every element is directly editable in PowerPoint               |
| 🤖 **Multi-Agent Pipeline**       | Planner → Generator → Refiner → Validator with LLM + rule-based dual mode                        |
| 📊 **Smart Charts**               | 8 chart types with automatic template color adaptation                                           |
| ✅ **3-Level Validation**          | Layout overflow/overlap → Template compliance → Content completeness                             |

***

## 🌟 概述

**组会PPT智能体**是一款面向科研组会场景的PPT自动制作工具，支持任意格式的过程文件输入，严格遵循用户提供的实验室模板，输出原生可编辑的PPTX。

### 核心卖点

| 卖点             | 说明                                                  |
| -------------- | --------------------------------------------------- |
| 🎨 **严格遵循模板**  | 模板DNA提取技术，从OOXML深度解析配色、字体、布局、装饰元素                   |
| 📄 **任意文件都能吃** | 支持PDF/Word/Markdown/纯文本/图片/Excel等混合格式               |
| ✏️ **原生可编辑**   | 输出真实PPTX，每个元素都可在PowerPoint中直接编辑                     |
| 🤖 **多智能体协作**  | Planner → Generator → Refiner → Validator，LLM+规则双模式 |
| 📊 **智能图表**    | 8种图表类型，自动适配模板配色                                     |
| ✅ **三级验证**     | 布局溢出/重叠 → 模板合规 → 内容完整性                              |

***

## 🏗️ Technical Architecture / 技术架构

### Five-Layer Architecture / 五层架构

```
┌──────────────────────────────────────────────────────────────────┐
│                        System Architecture                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Input Layer / 输入层                                      │   │
│  │  PDF/DOCX/MD/TXT/PNG/XLSX + Template PPTX (opt) + Config │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Parsing Layer / 解析层                                    │   │
│  │  ┌──────────────────┐  ┌──────────────────────────┐      │   │
│  │  │ Document Parser   │  │ Template DNA Extractor   │      │   │
│  │  │ MarkItDown/Docling│  │ OOXML Deep Parse         │      │   │
│  │  │  → Markdown       │  │  → Theme/Font/Layout     │      │   │
│  │  └──────────────────┘  └──────────────────────────┘      │   │
│  │  ┌──────────────────────────────────────────────────┐     │   │
│  │  │ LLM Content Structuring Engine                    │     │   │
│  │  │ Markdown → Type Detection → Info Extraction →     │     │   │
│  │  │ Unified PPT Structure                             │     │   │
│  │  └──────────────────────────────────────────────────┘     │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Multi-Agent Layer / 多智能体层                             │   │
│  │  Planner → Generator → Refiner → Validator               │   │
│  │  (规划)    (生成)      (优化)      (验证)                  │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Generation Layer / 生成层                                  │   │
│  │  python-pptx + matplotlib + Style Lock + Layout Engine    │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Output Layer / 输出层                                      │   │
│  │  PPTX (native editable) + Speaker Notes + Quality Report  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Four-Phase Workflow / 四阶段工作流

```
Phase 1: Input & Parsing / 输入与解析
├── Receive input: documents + template (opt) + config
├── Universal document parsing: MarkItDown → Markdown
├── Template DNA extraction: OOXML parsing → TemplateDNA
└── LLM content structuring: type detection → unified PPT structure

Phase 2: Intelligent Planning / 智能规划
├── Planner Agent: page allocation, layout selection, chart planning
└── User confirmation/adjustment of outline ← Key interaction point

Phase 3: Generation & Optimization / 生成与优化
├── Generator Agent: text generation, chart generation, slide assembly
├── Refiner Agent: quality check, expression optimization
└── Style Lock: color mapping, font replacement, decoration replication

Phase 4: Validation & Delivery / 验证与交付
├── Validator Agent: layout validation, template check, content completeness
├── Auto-fix (up to 3 rounds)
└── Output: PPTX + Speaker Notes + Quality Report
```

### Unified Narrative Structure / 统一叙事结构

All document types share the same framework / 所有文档类型共用同一套框架：

```
Page 1     Cover       Title + Author + Date / 封面
Page 2     Overview    Core content in one page / 概述
Page 3~N   Body        Auto-split by document logic (3-8 pages) / 主体
Page N+1   Summary     Key findings/conclusions / 总结
Page N+2   Discussion  Next steps / open questions / 讨论
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
├── src/
│   ├── __init__.py
│   ├── agent.py                  # Main entry / 主入口
│   ├── models.py                 # Data models / 数据模型
│   │
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── document_parser.py    # Universal document parser / 通用文档解析
│   │   ├── template_extractor.py # Template DNA extractor / 模板DNA提取
│   │   └── content_structurer.py # LLM content structuring / LLM内容结构化
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── planner.py            # Planning agent / 规划智能体
│   │   ├── generator.py          # Generation agent / 生成智能体
│   │   ├── refiner.py            # Refinement agent / 优化智能体
│   │   └── validator.py          # Validation agent / 验证智能体
│   │
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── pptx_builder.py       # PPTX builder / PPTX构建器
│   │   ├── chart_generator.py    # Chart generator / 图表生成器
│   │   ├── style_lock.py         # Style lock engine / 样式锁定引擎
│   │   └── layout_engine.py      # Layout engine / 布局引擎
│   │
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── layout_validator.py   # Layout validation (L1) / 布局验证
│   │   ├── compliance_checker.py # Compliance check (L2) / 合规检查
│   │   └── content_checker.py    # Content check (L3) / 内容检查
│   │
│   └── templates/
│       ├── create_template.py    # Template generator / 模板生成脚本
│       └── default_academic.pptx # Default template / 默认学术模板
│
└── tests/
    └── test_all.py               # Test suite / 测试套件
```

***

## 🚀 Installation / 安装

### Prerequisites / 前置条件

- Python 3.10+
- pip

### Quick Install / 快速安装

```bash
# Clone the repository / 克隆仓库
git clone https://github.com/YOUR_USERNAME/group-meeting-ppt-agent.git
cd group-meeting-ppt-agent

# Install dependencies / 安装依赖
pip install -r requirements.txt
```

### Dependencies / 依赖说明

| Package       | Purpose                                        |
| ------------- | ---------------------------------------------- |
| `python-pptx` | PPTX read/write and OOXML manipulation         |
| `matplotlib`  | Chart rendering with template color adaptation |
| `pandas`      | Table data processing                          |
| `Pillow`      | Image processing                               |
| `openai`      | LLM API integration (optional)                 |
| `lxml`        | XML parsing for OOXML deep extraction          |
| `markitdown`  | Universal document → Markdown conversion       |

### Optional Dependencies / 可选依赖

```bash
# For complex PDF parsing / 复杂PDF深度解析
pip install docling

# For development / 开发环境
pip install pytest pytest-cov
```

***

## 📖 Usage / 使用方法

### Command Line / 命令行

```bash
# Basic usage (rule-based, no LLM) / 基本用法（规则引擎，无需LLM）
python -m src.agent input.md --skip-llm -a "Author Name" -o ./output

# With template / 使用模板
python -m src.agent input.pdf -t lab_template.pptx --skip-llm -a "张三"

# With LLM (requires API key) / 使用LLM（需要API Key）
python -m src.agent input.md --api-key sk-xxx --model gpt-4o -a "张三"

# Preview outline only / 仅预览大纲
python -m src.agent input.md --outline-only --skip-llm

# Multiple input files / 多文件输入
python -m src.agent experiment.md data.xlsx notes.md --skip-llm -a "张三"
```

### Python API / Python接口

```python
from src.agent import GroupMeetingPPTAgent, GenerationConfig

# Configure / 配置
config = GenerationConfig(
    author="张三",
    date="2025-01-01",
    output_dir="./output",
    template_path="lab_template.pptx",  # optional
    skip_llm=True,                       # use rule-based engine
)

# Create agent and generate / 创建智能体并生成
agent = GroupMeetingPPTAgent(config=config)

# Preview outline / 预览大纲
outline = agent.get_outline(["experiment.md"])
print(agent.format_outline(outline))

# Generate PPTX / 生成PPTX
result = agent.generate(["experiment.md"], config)
print(f"Output: {result.pptx_path}")
print(f"Pages: {len(result.presentation.slides)}")
print(f"Template compliance: {result.compliance.overall_score:.0%}")
```

### CLI Parameters / 命令行参数

| Parameter          | Description                             | Default    |
| ------------------ | --------------------------------------- | ---------- |
| `input_files`      | Input file paths (positional, required) | -          |
| `-t, --template`   | Template PPTX path                      | None       |
| `-a, --author`     | Presenter name                          | ""         |
| `-d, --date`       | Date string                             | auto       |
| `-o, --output-dir` | Output directory                        | `./output` |
| `--api-key`        | OpenAI API key                          | None       |
| `--model`          | LLM model name                          | `gpt-4o`   |
| `--skip-llm`       | Skip LLM, use rule-based only           | False      |
| `--outline-only`   | Only print outline, don't generate PPTX | False      |

***

## 🧩 Core Modules / 核心模块

### 1. Universal Document Parser / 通用文档解析器

Smart routing between MarkItDown and Docling / MarkItDown与Docling智能路由：

- **Default**: MarkItDown (fast, broad format support)
- **Auto-switch to Docling**: When PDF > 5MB or table count > 5
- **Supported formats**: PDF, DOCX, XLSX, PPTX, MD, TXT, CSV, JSON, HTML, PNG, JPG, BMP, TIFF

### 2. Template DNA Extractor / 模板DNA提取引擎

Deep OOXML parsing to extract complete design specifications / OOXML深度解析提取完整设计规范：

- **Theme Colors**: From `theme1.xml` clrScheme (accent1-6, bg1-2, tx1-2)
- **Font Hierarchy**: majorFont/minorFont with Latin + East Asian support
- **Layout Structures**: Slide layout placeholder positions and types
- **Decorations**: Logo, header/footer elements, divider lines
- **Media**: All embedded media resources

### 3. Multi-Agent Pipeline / 多智能体协作

```
┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│  Planner   │───→│ Generator  │───→│  Refiner   │───→│ Validator  │
│            │    │            │    │            │    │            │
│ ·Page plan │    │ ·Text gen  │    │ ·Quality   │    │ ·Layout    │
│ ·Layout    │    │ ·Chart gen │    │ ·Optimize  │    │ ·Template  │
│ ·Chart     │    │ ·Assembly  │    │ ·Unify     │    │ ·Content   │
│ ·Confirm   │    │ ·Style     │    │ ·Trim      │    │ ·Score     │
└────────────┘    └────────────┘    └────────────┘    └────────────┘
```

Each agent supports **LLM mode** (with API key) and **rule-based mode** (without LLM).

### 4. Chart Generator / 图表生成器

8 chart types with automatic template color adaptation / 8种图表类型，自动适配模板配色：

| Chart                  | Use Case                               |
| ---------------------- | -------------------------------------- |
| `comparison_table`     | Highlighted comparison tables          |
| `progress_chart`       | Milestone visualization                |
| `metric_dashboard`     | Big-number KPI display                 |
| `timeline`             | Chronological events                   |
| `sota_comparison`      | State-of-the-art horizontal bar chart  |
| `ablation_chart`       | Ablation study with baseline highlight |
| `training_curves`      | Multi-line training metrics            |
| `architecture_diagram` | Pipeline/architecture flow diagram     |

### 5. Style Lock Engine / 样式锁定引擎

Ensures generated PPTX strictly follows template DNA / 确保生成PPT严格遵循模板DNA：

- **Color Remapping**: Non-compliant colors → template palette
- **Font Replacement**: Title/body font hierarchy enforcement
- **Dimension Calibration**: Overflow prevention and boundary correction
- **Decoration Replication**: Logo, footer, divider line reproduction

### 6. 3-Level Validation / 三级验证

| Level   | Validation                                         | Pass Condition |
| ------- | -------------------------------------------------- | -------------- |
| Level 1 | Layout (overflow/overlap/blank)                    | Issues = 0     |
| Level 2 | Template compliance (color/font/layout/decoration) | Score ≥ 90%    |
| Level 3 | Content (placeholder/completeness/structure)       | No P0 issues   |

***

## 📊 Supported Slide Layouts / 支持的幻灯片布局

| Layout         | Description                                |
| -------------- | ------------------------------------------ |
| `cover`        | Title slide with author, date, accent line |
| `bullet_list`  | Standard bullet point content slide        |
| `two_column`   | Two-column comparison with divider         |
| `chart`        | Chart image with caption area              |
| `table`        | Formatted table with styled headers        |
| `image_grid`   | Auto-layout image grid (2-8 images)        |
| `architecture` | Block diagram with arrows                  |
| `summary`      | Centered title with checkmark points       |
| `discussion`   | Centered title with arrow points           |

***

## 🧪 Testing / 测试

```bash
# Run all tests / 运行所有测试
python tests/test_all.py

# Test coverage / 测试覆盖
# - Models (12 data classes)
# - Document Parser (MD/TXT parsing)
# - Content Structurer (fallback mode)
# - Planner (rule-based)
# - Refiner (text trimming, dedup)
# - Validator (structure validation)
# - PPTX Builder (6-slide generation)
# - Chart Generator (bar + SOTA chart)
# - Layout Engine (9 layout types)
# - End-to-end flow (full pipeline)
```

***

## 🛠️ Tech Stack / 技术栈

| Module           | Technology  | Purpose                               |
| ---------------- | ----------- | ------------------------------------- |
| Document Parsing | MarkItDown  | Universal format → Markdown (default) |
| Document Parsing | Docling     | Complex PDF deep parsing (fallback)   |
| Template/PPT     | python-pptx | PPTX read/write, OOXML manipulation   |
| Charts           | matplotlib  | Data chart rendering                  |
| LLM              | OpenAI API  | Content structuring & optimization    |
| Data             | pandas      | Table data processing                 |
| Image            | Pillow      | Image processing & OCR                |
| XML              | lxml        | OOXML deep parsing                    |

***

## 📝 Default Theme / 默认主题配色

```python
DEFAULT_THEME = {
    "primary": "#1E3A5F",      # Deep Blue / 深蓝
    "secondary": "#4A6FA5",    # Medium Blue / 中蓝
    "accent": "#E85D4E",       # Coral Red / 珊瑚红
    "background": "#F8F9FA",   # Light Gray / 浅灰白
    "text": "#2C3E50",         # Dark Gray / 深灰
}

DEFAULT_FONTS = {
    "title": "Source Han Serif SC",   # 思源宋体
    "body": "Source Han Sans SC",     # 思源黑体
    "mono": "Consolas",
}
```

***

## 🤝 Contributing / 贡献

Contributions are welcome! Please feel free to submit a Pull Request.

欢迎贡献代码！请随时提交 Pull Request。

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

***

## 📄 License / 许可证

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

本项目基于 MIT 许可证开源，详见 [LICENSE](LICENSE) 文件。

***

## 🙏 Acknowledgments / 致谢

| Project                                                        | Contribution                             |
| -------------------------------------------------------------- | ---------------------------------------- |
| [ppt-master](https://github.com/hugohe3/ppt-master)            | Template DNA extraction, SVG→native PPTX |
| [MarkItDown](https://github.com/microsoft/markitdown)          | Universal document → Markdown conversion |
| [Docling](https://github.com/docling-project/docling)          | Complex PDF deep parsing                 |
| [Auto-Slides](https://github.com/Westlake-AGI-Lab/Auto-Slides) | Multi-agent collaboration pattern        |
| [pptx-generator](https://github.com/paul0728/pptx-generator)   | Slide type schema design                 |

***

## ⚠️ Known Limitations / 已知限制

- LLM mode requires OpenAI API key (or compatible API)
- Complex template decorations may not be perfectly replicated
- Architecture diagram is block-based; complex diagrams need manual adjustment
- Chinese fonts (Source Han) must be installed on the system for correct rendering

***

<div align="center">

**Made with ❤️ for researchers who hate making PPTs**

**用 ❤️ 为讨厌做PPT的科研人打造**

</div>
