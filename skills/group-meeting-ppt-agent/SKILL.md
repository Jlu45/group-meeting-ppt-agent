---
name: group-meeting-ppt-agent
description: 从过程文件自动生成严格遵循实验室模板的组会 PPTX
version: 1.0.0
triggers:
  - "生成组会PPT"
  - "制作PPT"
  - "generate meeting slides"
  - "make presentation"
  - "组会幻灯片"
  - "汇报PPT"
---

# 组会PPT智能体

你是一个科研组会 PPT 制作专家。你需要从用户提供的过程文件中提取信息，生成符合实验室模板的原生可编辑 PPTX。

## 禁止事项

- 不要在工具脚本中调用 OpenAI / Anthropic API
- 不要硬编码 PPT 坐标，除非模板没有可用 Layout
- 不要把所有内容堆在一页
- 不要输出 PDF 或图片版 PPT
- 不要忽略模板的母版、版式和占位符

## 必须遵循

1. 先识别文件类型和用途
2. 再解析文件内容
3. 再构建 Semantic Asset Store
4. 再解析模板 DNA
5. 再规划 SlideSpec
6. 最后调用渲染工具生成 PPTX
7. 生成后必须调用验证工具
8. 如果验证失败，最多自动修复 3 轮

## 输入格式

```json
{
  "files": ["path/to/file1.pdf", "path/to/file2.docx", "path/to/fig.png"],
  "template": "path/to/lab_template.pptx",
  "constraints": {
    "author": "张三",
    "date": "2026-05-15",
    "language": "zh",
    "target_slide_count": 15,
    "max_slide_count": 20,
    "template_mode": "fidelity",
    "style_preference": "academic",
    "must_include": ["实验结果", "下一步计划"],
    "must_exclude": []
  }
}
```

## 输出格式

```json
{
  "pptx_path": "output/group_meeting.pptx",
  "quality_report": {
    "overall_score": 85.5,
    "grade": "B",
    "structure_score": 90,
    "layout_score": 85,
    "compliance_score": 80,
    "content_score": 87,
    "issue_summary": {
      "total": 3,
      "by_severity": {"warning": 2, "info": 1},
      "by_level": {"layout": 2, "compliance": 1}
    }
  },
  "slide_count": 14,
  "render_log": {
    "slide_count": 14,
    "layout_usage": {"layout1": 5, "layout2": 3},
    "warnings": [],
    "errors": []
  }
}
```

## 工作流（5 个阶段）

### 阶段 1：文件识别（File Recognition）

识别每个输入文件的类型、用途和 PPT 角色。

```bash
python -m src.tools.recognize_files \
  path/to/file1.pdf path/to/file2.docx \
  --output .cache/file_recognition.json
```

也可以通过 stdin 传入 JSON 数组：

```bash
echo '["path/to/file1.pdf", "path/to/file2.docx"]' | \
  python -m src.tools.recognize_files --output .cache/file_recognition.json
```

或通过 `--input-json` 传入：

```bash
python -m src.tools.recognize_files \
  --input-json .cache/input_files.json \
  --output .cache/file_recognition.json
```

**输出 JSON Schema：**

```json
{
  "files": [
    {
      "id": "frec-xxxxxxxx",
      "path": "绝对路径",
      "filename": "文件名",
      "extension": ".pdf",
      "base_type": "document",
      "content_type": "experiment_log",
      "ppt_purpose": "method_and_result",
      "confidence": 0.85,
      "sequence_number": null,
      "date": "2026-05-15",
      "version": null,
      "suggested_parser": "UniversalDocumentParser",
      "suggested_slide_types": ["method", "result", "discussion"]
    }
  ],
  "total": 2
}
```

### 阶段 2：内容解析（Document Parsing）

将每个文件解析为 Markdown 格式。

```bash
python -m src.tools.parse_documents \
  path/to/file1.pdf path/to/file2.docx \
  --output .cache/parsed_documents.json
```

**输出 JSON Schema：**

```json
{
  "documents": [
    {
      "source_path": "绝对路径",
      "file_type": "pdf",
      "markdown_content": "解析后的 Markdown 内容...",
      "content_length": 5230
    }
  ],
  "total": 2,
  "errors": []
}
```

### 阶段 3：模板 DNA 提取（Template DNA Extraction）

从模板 PPTX 中提取版式、占位符、主题、装饰元素等结构信息。

```bash
python -m src.tools.extract_template_dna \
  path/to/lab_template.pptx \
  --output .cache/template_dna.json
```

**输出 JSON Schema：**

```json
{
  "slide_width": 10.0,
  "slide_height": 7.5,
  "theme": {
    "name": "Office",
    "colors": { "accent1": "#4472C4", "bg1": "#FFFFFF", "tx1": "#000000" },
    "fonts": { "major_latin": "Calibri", "minor_latin": "Calibri" }
  },
  "masters": [...],
  "layouts": [
    {
      "id": "slideLayout1",
      "name": "Title Slide",
      "layout_type": "cover",
      "placeholders": [...],
      "decorations": [...],
      "tags": ["cover"]
    }
  ],
  "decorations": [...],
  "media": {},
  "source_path": "path/to/lab_template.pptx",
  "layout_summary": [
    {
      "id": "slideLayout1",
      "name": "Title Slide",
      "layout_type": "cover",
      "placeholder_count": 2,
      "tags": ["cover"]
    }
  ]
}
```

### 阶段 4：规划与渲染（Planning & Rendering）

**此阶段由 AI 编程助手负责**。你需要：

1. 根据解析内容和文件识别结果，使用 `planning_prompt.md` 生成 SlideSpec 数组
2. 将 SlideSpec、TemplateDNA、AssetStore、UserConstraints 组装为 SharedState JSON
3. 调用渲染工具生成 PPTX

```bash
python -m src.tools.render_pptx \
  --state .cache/shared_state.json \
  --output output/group_meeting.pptx
```

**SharedState JSON Schema（输入）：**

```json
{
  "user_constraints": {
    "author": "张三",
    "date": "2026-05-15",
    "language": "zh",
    "target_slide_count": 15,
    "max_slide_count": 20,
    "template_mode": "fidelity"
  },
  "file_recognition": [...],
  "asset_store": {
    "source_files": {},
    "evidences": {},
    "content_units": {},
    "tables": {},
    "figures": {},
    "code": {},
    "metrics": {}
  },
  "template_dna": { ... },
  "slide_specs": [
    {
      "id": "slide_001",
      "slide_type": "cover",
      "title": "液压灵巧手组会汇报",
      "message": "2026年5月15日",
      "elements": [
        {"role": "slide_title", "content": "液压灵巧手组会汇报", "asset_ids": [], "required": true, "visual_weight": 10},
        {"role": "subtitle", "content": "张三 | 2026-05-15", "asset_ids": [], "required": true, "visual_weight": 5}
      ],
      "intent": {
        "slide_type": "cover",
        "content_roles": ["slide_title", "subtitle"],
        "density": "low",
        "preferred_layout": null,
        "must_have": ["slide_title"]
      },
      "candidate_layout_ids": [],
      "selected_layout_id": null,
      "speaker_notes": ""
    }
  ],
  "render_log": {},
  "validation_issues": [],
  "quality_report": {}
}
```

### 阶段 5：验证与修复（Validation & Repair）

验证生成的 PPTX 质量，必要时进行修复。

```bash
python -m src.tools.validate_pptx \
  output/group_meeting.pptx \
  --template-dna .cache/template_dna.json \
  --output output/quality_report.json
```

**输出 JSON Schema：**

```json
{
  "pptx_path": "output/group_meeting.pptx",
  "quality_report": {
    "structure_score": 90,
    "layout_score": 85,
    "compliance_score": 80,
    "content_score": 87,
    "overall_score": 85.5,
    "grade": "B",
    "slide_count": 14,
    "issue_summary": {
      "total": 3,
      "by_severity": {"warning": 2, "info": 1},
      "by_level": {"layout": 2, "compliance": 1},
      "by_type": {"margin_violation": 1, "font_mismatch": 1, "element_overlap": 1}
    }
  },
  "issues": [
    {
      "id": "xxxxxxxx",
      "severity": "warning",
      "slide_id": "slide_3",
      "element_id": "2",
      "issue_type": "margin_violation",
      "message": "第3张幻灯片元素超出右边界",
      "suggested_fix": "调整元素宽度或位置"
    }
  ],
  "issue_count": 3,
  "grade": "B",
  "overall_score": 85.5
}
```

## 默认组会叙事结构

1. **封面**（cover）— 标题、汇报人、日期
2. **概述**（overview）— 本周核心进展摘要
3. **背景/目标**（background）— 研究背景或目标回顾
4. **方法/方案**（method）— 方法论、实验设置、技术方案
5. **主结果**（result）— 核心实验结果
6. **补充结果**（supplementary）— 对比实验、消融实验
7. **问题分析**（analysis）— 遇到的问题与原因分析
8. **下一步计划**（next_step）— 后续工作安排
9. **讨论**（discussion）— 开放讨论

## 质量等级标准

| 等级 | 分数范围 | 说明 |
|------|----------|------|
| A | ≥ 85 | 可直接使用 |
| B | 70-84 | 需少量手动调整 |
| C | 60-69 | 需较多修改 |
| D | < 60 | 需重新生成 |

## 完整示例

```bash
# 阶段 1：文件识别
python -m src.tools.recognize_files \
  测试/液压灵巧手/4月21日Ansys仿真记录.docx \
  测试/液压灵巧手/MC3/7000_06048_MC3功能.pdf \
  --output .cache/file_recognition.json

# 阶段 2：内容解析
python -m src.tools.parse_documents \
  测试/液压灵巧手/4月21日Ansys仿真记录.docx \
  测试/液压灵巧手/MC3/7000_06048_MC3功能.pdf \
  --output .cache/parsed_documents.json

# 阶段 3：模板 DNA 提取
python -m src.tools.extract_template_dna \
  src/templates/default_academic.pptx \
  --output .cache/template_dna.json

# 阶段 4：AI 编程助手规划 SlideSpec → 组装 SharedState → 渲染
# （AI 编程助手根据 planning_prompt.md 生成 slide_specs）
python -m src.tools.render_pptx \
  --state .cache/shared_state.json \
  --output output/group_meeting.pptx

# 阶段 5：验证
python -m src.tools.validate_pptx \
  output/group_meeting.pptx \
  --template-dna .cache/template_dna.json \
  --output output/quality_report.json
```

## 修复循环

如果验证结果 grade < B，执行修复循环：

1. 读取 `quality_report.json` 中的 issues
2. 使用 `refinement_prompt.md` 生成修复后的 SlideSpec
3. 更新 SharedState 中的 `slide_specs` 和 `validation_issues`
4. 重新调用 `render_pptx` 渲染
5. 重新调用 `validate_pptx` 验证
6. 最多重复 3 轮
