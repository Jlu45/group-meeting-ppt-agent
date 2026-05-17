# 组会PPT智能体 - 约束规则

## 核心约束

### 1. 禁止LLM API调用
- 所有工具脚本（`src/tools/` 目录下）不得调用任何LLM API（包括OpenAI、Anthropic、本地模型等）
- 幻灯片规划必须使用规则引擎，不得依赖LLM生成内容
- 如需LLM增强，仅允许在 `skills/group-meeting-ppt-agent/prompts/` 中提供提示词模板，由AI IDE在独立步骤中调用

### 2. 禁止硬编码PPT坐标
- 除非无模板布局可用（即 `template_dna.layouts` 为空），否则不得在渲染代码中硬编码任何PPT坐标
- 所有坐标必须来源于模板DNA（`TemplateDNA`）中的 `LayoutSpec` 和 `PlaceholderSpec`
- 回退布局（fallback layouts）仅作为最后手段使用

### 3. 必须遵循8步流水线
整个生成流程必须严格按照以下8步执行，每步输出中间JSON到 `.cache` 目录：

| 步骤 | 名称 | 输出文件 |
|------|------|----------|
| Step 1 | 文件识别 | `.cache/file_recognition.json` |
| Step 2 | 文档解析 | `.cache/parsed_documents.json` |
| Step 3 | 资产构建 | `.cache/asset_store.json` |
| Step 4 | 模板DNA提取 | `.cache/template_dna.json` |
| Step 5 | 幻灯片规划 | `.cache/slide_spec.json` |
| Step 6 | 密度控制 | `.cache/slide_spec_controlled.json` |
| Step 7 | 渲染PPTX | 输出 `.pptx` 文件 |
| Step 8 | 验证与质量报告 | `.cache/quality_report.json` |

不得跳过任何步骤，不得更改步骤顺序。

### 4. 渲染后必须验证
- Step 7（渲染）完成后，必须执行 Step 8（验证）
- 验证必须使用 `VisualValidator` 进行结构、布局、合规性和内容四层检测
- 必须使用 `QualityReporter` 生成质量报告

### 5. 最大修复轮数
- 自动修复最多执行 **3轮**
- 超过3轮仍未修复的问题标记为"需人工处理"
- 修复轮数可通过 `--max-fix-rounds` 参数调整，但默认值和上限均为3

### 6. 模板模式默认值
- `template_mode` 默认为 `"fidelity"`（高保真模式）
- 高保真模式下，渲染器必须优先使用模板中的布局和占位符
- 仅在模板布局完全不可用时才使用回退布局

## 密度限制

| 指标 | 限制值 |
|------|--------|
| 每页最大要点数 | 6 条 |
| 每条要点最大字符数 | 80 字符 |
| 标题最大字符数 | 40 字符 |

超出限制的内容由 `DensityController` 自动截断或拆分。

## 最小字号限制

| 元素类型 | 最小字号 |
|----------|----------|
| 标题 | 24pt |
| 正文 | 16pt |
| 表格 | 10pt |

低于最小字号的文本将在验证阶段被标记为 `font_too_small` 问题。

## 中间文件规范

- 所有中间JSON文件必须保存到输出目录下的 `.cache/` 子目录
- JSON文件使用 UTF-8 编码，`ensure_ascii=False`
- 每个JSON文件必须符合 `schemas/` 目录下对应的JSON Schema
- AI IDE可通过读取 `.cache/` 中的文件进行增量编辑和调试

## 代码规范

- Python代码不得包含LLM API调用（`openai`、`anthropic` 等import）
- 数据模型必须使用 `src.common.models` 中定义的dataclass
- JSON序列化/反序列化必须使用 `src.common.json_io` 中的工具函数
- 每个工具脚本必须支持CLI调用和程序化调用两种方式
