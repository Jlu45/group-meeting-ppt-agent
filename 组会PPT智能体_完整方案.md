# 组会PPT自动制作智能体 — 完整方案

---

## 一、产品定位

### 1.1 一句话定义

**组会PPT智能体**是一款面向科研组会场景的PPT自动制作工具，支持任意格式的过程文件输入，严格遵循用户提供的实验室模板，输出原生可编辑的PPTX。

### 1.2 核心卖点

| 卖点 | 说明 |
|-----|------|
| **严格遵循模板** | 模板DNA提取技术，从OOXML深度解析配色、字体、布局、装饰元素 |
| **任意文件都能吃** | 支持PDF/Word/Markdown/纯文本/图片/Excel等混合格式 |
| **原生可编辑** | 输出真实PPTX，每个元素都可在PowerPoint中直接编辑 |

### 1.3 差异化定位

```
                    模板遵循度
                    高
                    │    ★ 我们
                    │  （严格模板 + 通用输入 + 可编辑）
                    │
                    │      ppt-master
                    │    （模板强，但无组会优化）
                    │
                    │  PPT_generate
                    │  （模板中，输入通用）
                    │
                    │────────────────────────────────
                    │     Paper2PPT / Auto-Slides
                    │   （学术强，但输出PDF，模板弱）
                    低
                     低              输入通用性              高
```

### 1.4 目标用户

| 用户 | 场景 | 输入文件 |
|-----|------|---------|
| 研究生 | 每周组会汇报实验进展 | 实验记录(MD)、数据表格(XLSX) |
| 研究生 | 文献分享 | 论文PDF、阅读笔记(MD) |
| 项目负责人 | 项目进展汇报 | 进展报告(DOCX)、里程碑表格 |
| 工程师 | 技术方案评审 | 设计文档(MD)、架构图(PNG) |

---

## 二、技术调研结论

### 2.1 关键参考项目

| 项目 | Stars | 核心借鉴 |
|-----|-------|---------|
| [ppt-master](https://github.com/hugohe3/ppt-master) | 10.6k | 模板DNA提取、SVG→原生PPTX、后处理验证 |
| [MarkItDown](https://github.com/microsoft/markitdown) | 82.6k | 通用文档→Markdown、多格式支持 |
| [Docling](https://github.com/docling-project/docling) | 42.6k | 复杂PDF深度解析、表格/布局保真 |
| [Auto-Slides](https://github.com/Westlake-AGI-Lab/Auto-Slides) | - | 多智能体协作、Planner→Generator→Refiner |
| [pptx-generator](https://github.com/paul0728/pptx-generator) | - | 11种幻灯片类型、slides.json schema |

### 2.2 文档解析器选型

| 解析器 | Stars | 支持格式 | 推荐场景 |
|-------|-------|---------|---------|
| **MarkItDown** | 82.6k | PDF/DOCX/MD/HTML/XLSX/图片OCR | **默认首选** |
| **Docling** | 42.6k | PDF/DOCX/PPTX/XLSX/HTML/图片 | 复杂PDF备选 |

**策略**：默认MarkItDown，复杂PDF（>5MB或表格>5个）自动切换Docling。

### 2.3 模板处理技术

| 方案 | 优点 | 缺点 | 选择 |
|-----|------|------|------|
| python-pptx编辑 | 成熟稳定 | 复杂模板适配有限 | 有模板时使用 |
| pptxgenjs生成 | 灵活强大 | 需从零构建 | 无模板时使用 |
| **OOXML深度解析** | 完全控制 | 实现复杂 | **模板DNA提取** |

---

## 三、系统架构

### 3.1 五层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         系统架构                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 输入层                                                   │   │
│  │  PDF/DOCX/MD/TXT/PNG/XLSX  +  模板PPTX(可选)  +  配置    │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 解析层                                                   │   │
│  │  ┌─────────────────┐    ┌─────────────────────────┐     │   │
│  │  │ 通用文档解析器   │    │ 模板DNA提取引擎         │     │   │
│  │  │ MarkItDown/Docling│   │ OOXML深度解析           │     │   │
│  │  │  → Markdown      │    │  → Theme/Font/Layout    │     │   │
│  │  └─────────────────┘    └─────────────────────────┘     │   │
│  │  ┌─────────────────────────────────────────────────┐     │   │
│  │  │ LLM内容结构化引擎                                │     │   │
│  │  │ Markdown → 识别类型 → 提取信息 → 统一PPT结构    │     │   │
│  │  └─────────────────────────────────────────────────┘     │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 多智能体层                                               │   │
│  │  Planner → Generator → Refiner → Validator              │   │
│  │  (规划)    (生成)      (优化)      (验证)                │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 生成层                                                   │   │
│  │  python-pptx + matplotlib + 样式锁定引擎 + QA验证引擎    │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 输出层                                                   │   │
│  │  组会PPT.pptx (原生可编辑) + 演讲者备注                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 统一叙事结构

所有文档类型共用同一套框架：

```
第1页    封面      主题 + 汇报人 + 日期
第2页    概述      1页讲清楚核心内容
第3~N页  主体      按文档逻辑自动分页（通常3-8页）
倒数第2页 总结      关键发现/进展/结论
最后1页   讨论      下一步计划 / 待解决问题
```

**不同文档的内容映射**：

| 框架位置 | 进展报告 | 实验记录 | 文献笔记 | 技术方案 |
|---------|---------|---------|---------|---------|
| 封面 | Q3项目进展 | XX实验结果 | 论文精读：XXX | XX系统设计方案 |
| 主体 | 各模块进展→问题风险 | 方法→结果→分析 | 背景→方法→启发 | 需求→设计→验证 |
| 总结 | 成果总结 | 实验结论 | 论文贡献 | 方案优势 |
| 讨论 | 下季度计划 | 后续方向 | 对我们的启发 | 待确认事项 |

---

## 四、核心模块设计

### 4.1 通用文档解析器

```python
class UniversalDocumentParser:
    """通用文档解析器 - 任意格式 → Markdown"""
    
    def __init__(self):
        self.markitdown = MarkItDown(enable_plugins=True)
        self.docling = DocumentConverter()
    
    def parse(self, file_path: str) -> ParsedDocument:
        ext = Path(file_path).suffix.lower()
        
        if ext == '.pdf':
            content = self._parse_pdf(file_path)
        elif ext in ['.docx', '.xlsx', '.png', '.jpg']:
            content = self.markitdown.convert(file_path).text_content
        else:
            content = self.markitdown.convert(file_path).text_content
        
        return ParsedDocument(
            source_path=file_path,
            markdown_content=content
        )
    
    def _parse_pdf(self, path: str) -> str:
        """PDF智能路由：简单用MarkItDown，复杂用Docling"""
        if os.path.getsize(path) > 5 * 1024 * 1024:
            return self.docling.convert(path).document.export_to_markdown()
        preview = self.markitdown.convert(path).text_content
        if preview.count('|---|') > 5:
            return self.docling.convert(path).document.export_to_markdown()
        return preview
```

### 4.2 LLM内容结构化引擎

```python
class ContentStructuringEngine:
    """文档类型无关的内容结构化"""
    
    PROMPT = """
    你是组会PPT内容规划专家。分析以下文档，输出JSON格式PPT大纲。
    
    文档内容：{content}
    
    输出要求：
    1. "doc_type": 文档类型（progress_report/experiment_log/literature_note/tech_design/other）
    2. "title": PPT标题
    3. "summary": 一句话概述
    4. "slides": 幻灯片数组，每页包含：
       - "title": 页面标题
       - "layout": 布局类型（cover/bullet_list/two_column/chart/table/image_grid/architecture）
       - "points": 要点数组（3-6个，每项一句话）
       - "table_data": 如有表格，提供JSON数组
       - "chart_desc": 如需图表，描述内容
       - "notes": 演讲者备注
    
    PPT结构（所有文档类型统一）：
    - 第1页: 封面
    - 第2页: 概述（1页讲清楚核心内容）
    - 第3页起: 主体内容（按文档逻辑分页）
    - 倒数第2页: 总结
    - 最后1页: 讨论（下一步计划/待解决问题）
    """
    
    def structure(self, parsed_doc: ParsedDocument) -> StructuredPresentation:
        response = self.llm.generate(
            prompt=self.PROMPT.format(content=parsed_doc.markdown_content[:12000]),
            response_format={"type": "json_object"}
        )
        data = json.loads(response)
        slides = self._ensure_unified_structure(data['slides'])
        return StructuredPresentation(
            doc_type=data.get('doc_type', 'other'),
            title=data['title'],
            summary=data.get('summary', ''),
            slides=slides
        )
    
    def _ensure_unified_structure(self, slides: list) -> list:
        """确保首尾符合统一叙事结构"""
        if slides[0].get('layout') != 'cover':
            slides.insert(0, {'title': '封面', 'layout': 'cover', 'points': []})
        if len(slides) >= 3:
            if slides[-2].get('title') != '总结':
                slides.insert(-1, {'title': '总结', 'layout': 'bullet_list', 'points': []})
            if slides[-1].get('title') not in ['讨论', '讨论与下一步']:
                slides.append({'title': '讨论与下一步', 'layout': 'bullet_list', 'points': []})
        return slides
```

### 4.3 模板DNA提取引擎

```python
class TemplateDNAExtractor:
    """从PPTX模板提取完整设计规范"""
    
    def extract(self, template_path: str) -> TemplateDNA:
        unpacked = self._unpack_pptx(template_path)
        
        return TemplateDNA(
            theme=self._extract_theme_colors(unpacked),
            fonts=self._extract_font_hierarchy(unpacked),
            layouts=self._extract_layout_structures(unpacked),
            decorations=self._analyze_decoration_patterns(unpacked),
            media=self._extract_media_relationships(unpacked)
        )
    
    def _extract_theme_colors(self, unpacked) -> ThemeColors:
        """从theme1.xml提取完整色板"""
        theme_xml = unpacked['ppt/theme/theme1.xml']
        return ThemeColors(
            primary=self._get_color(theme_xml, 'accent1'),
            secondary=self._get_color(theme_xml, 'accent2'),
            accent=self._get_color(theme_xml, 'accent3'),
            background=self._get_color(theme_xml, 'bg1'),
            text=self._get_color(theme_xml, 'tx1')
        )
    
    def _analyze_decoration_patterns(self, unpacked) -> DecorationPatterns:
        """分析装饰元素：Logo、页眉页脚、分隔线等"""
        return DecorationPatterns(
            logo=self._find_logo(unpacked),
            header=self._find_header_elements(unpacked),
            footer=self._find_footer_elements(unpacked),
            dividers=self._find_divider_lines(unpacked)
        )
```

### 4.4 样式锁定引擎

```python
class StyleLockEngine:
    """确保生成PPT严格遵循模板DNA"""
    
    def apply(self, slide, template_dna: TemplateDNA):
        slide = self._remap_colors(slide, template_dna.theme)
        slide = self._remap_fonts(slide, template_dna.fonts)
        slide = self._calibrate_dimensions(slide, template_dna)
        slide = self._apply_decorations(slide, template_dna.decorations)
        return slide
    
    def validate_compliance(self, output_path: str) -> ComplianceReport:
        return ComplianceReport(
            color_score=self._check_color_usage(output_path),
            font_score=self._check_font_usage(output_path),
            layout_score=self._check_layout_consistency(output_path),
            decoration_score=self._check_decorations(output_path)
        )
```

### 4.5 图表生成器

```python
class ChartGenerator:
    """通用+科研图表生成，配色适配模板"""
    
    def __init__(self, template_dna: TemplateDNA):
        self._setup_matplotlib(template_dna)
    
    # 组会通用图表
    def generate_comparison_table(self, data, headers, highlight_best=True): pass
    def generate_progress_chart(self, milestones): pass
    def generate_metric_dashboard(self, metrics): pass
    def generate_timeline(self, events): pass
    
    # 科研专用图表
    def generate_sota_comparison(self, data): pass
    def generate_ablation_chart(self, data, baseline): pass
    def generate_training_curves(self, metrics): pass
    def generate_architecture_diagram(self, architecture): pass
```

### 4.6 多智能体协作

```
┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│  Planner   │───→│ Generator  │───→│  Refiner   │───→│ Validator  │
│            │    │            │    │            │    │            │
│ ·页数规划   │    │ ·文本生成   │    │ ·质量检查   │    │ ·布局验证   │
│ ·布局选择   │    │ ·图表生成   │    │ ·表达优化   │    │ ·模板检查   │
│ ·图表决策   │    │ ·幻灯片组装 │    │ ·风格统一   │    │ ·内容完整   │
│ ·用户确认   │    │ ·样式应用   │    │ ·精简冗余   │    │ ·合规评分   │
└────────────┘    └────────────┘    └────────────┘    └────────────┘
```

---

## 五、工作流程

### 5.1 四阶段流程

```
Phase 1: 输入与解析
├── 接收输入：过程文件 + 模板(可选) + 配置
├── 通用文档解析：MarkItDown → Markdown
├── 模板DNA提取：OOXML解析 → TemplateDNA
└── LLM内容结构化：识别类型 → 统一PPT结构

Phase 2: 智能规划
├── Planner Agent：页数分配、布局选择、图表规划
└── 用户确认/调整大纲 ← 关键交互点

Phase 3: 生成与优化
├── Generator Agent：文本生成、图表生成、幻灯片组装
├── Refiner Agent：质量检查、表达优化
└── 样式锁定：颜色映射、字体替换、装饰复刻

Phase 4: 验证与交付
├── Validator Agent：布局验证、模板检查、内容完整
├── 自动修复（最多3轮）
└── 输出：PPTX + 演讲者备注 + 质量报告
```

### 5.2 用户交互示例

```
用户: 帮我把这个实验记录做成组会PPT [upload experiment_log.md]
      模板用这个 [upload lab_template.pptx]

智能体: 已解析文档。检测到【实验记录】。
       已提取模板DNA：主色#003366、思源宋体+思源黑体、Logo右上角。
       
       建议PPT结构（共10页）：
       1. 封面：XXX实验结果汇报
       2. 概述：实验目标与核心发现
       3. 实验设置
       4. 实验方法
       5. 主实验结果（含SOTA对比表）
       6. 消融实验（含柱状图）
       7. 可视化结果
       8. 总结
       9. 讨论
       
       请确认或调整：

用户: 第6页消融实验展开讲，可视化加一页

智能体: 已调整（共11页）。正在生成PPT...
       ✅ 完成！模板遵循度: 98%
       [下载 experiment_report.pptx]
```

---

## 六、技术栈

### 6.1 核心依赖

| 模块 | 技术 | 用途 |
|-----|------|------|
| 文档解析 | MarkItDown | 通用格式→Markdown（默认） |
| 文档解析 | Docling | 复杂PDF深度解析（备选） |
| 模板/PPT | python-pptx | PPTX读写、OOXML操作 |
| PPT生成 | pptxgenjs | 无模板时从零生成 |
| 图表 | matplotlib | 数据图表渲染 |
| LLM | OpenAI/Anthropic API | 内容结构化 |
| 数据处理 | pandas | 表格处理 |
| 图像 | Pillow | 图像处理与OCR |
| 验证 | markitdown | PPTX文本提取验证 |

### 6.2 安装命令

```bash
pip install markitdown python-pptx matplotlib pandas Pillow openai

# 可选
pip install docling
npm install -g pptxgenjs
```

### 6.3 默认模板配色

```javascript
const DEFAULT_THEME = {
  primary: '#1E3A5F',      // 深蓝
  secondary: '#4A6FA5',    // 中蓝
  accent: '#E85D4E',       // 珊瑚红
  background: '#F8F9FA',   // 浅灰白
  text: '#2C3E50'          // 深灰
};

const DEFAULT_FONTS = {
  title: 'Source Han Serif SC',   // 思源宋体
  body: 'Source Han Sans SC',     // 思源黑体
  mono: 'Consolas'
};
```

---

## 七、质量保障

### 7.1 三级验证

| 级别 | 验证内容 | 通过条件 |
|-----|---------|---------|
| Level 1 | 布局验证（溢出/重叠/空白页） | Issues = 0 |
| Level 2 | 模板遵循度（颜色/字体/布局/装饰） | 评分 ≥ 90% |
| Level 3 | 内容验证（占位符/完整性/术语） | 无P0问题 |

### 7.2 自动修复

```
验证失败
    ↓
修复#1: fix_pptx.py自动修复 → 重新验证
    ↓ (仍失败)
修复#2: LLM辅助修复 → 重新验证
    ↓ (仍失败)
修复#3: 记录问题 → 输出最佳版本 → 向用户报告
```

---

## 八、实现路线图

### Phase 1: 基础框架（第1-3周）

| 周次 | 任务 | 交付物 |
|-----|------|-------|
| W1 | 通用文档解析器、模板DNA提取 | UniversalDocumentParser、TemplateDNAExtractor |
| W2 | LLM内容结构化、python-pptx基础框架 | ContentStructuringEngine、基础PPTX生成 |
| W3 | 默认学术模板、端到端demo | 内置模板.pptx、可运行demo |

### Phase 2: 核心功能（第4-7周）

| 周次 | 任务 | 交付物 |
|-----|------|-------|
| W4 | 多智能体框架、图表生成器 | 4个Agent、ChartGenerator |
| W5 | 样式锁定引擎、布局决策引擎 | StyleLockEngine、LayoutEngine |
| W6 | 用户交互流程、智能分页 | 交互式生成、ContentAdaptiveEngine |
| W7 | 质量验证流程 | 三级验证+自动修复 |

### Phase 3: 模板优化（第8-10周）

| 周次 | 任务 | 交付物 |
|-----|------|-------|
| W8 | 复杂模板适配、装饰元素复刻 | 高级模板支持 |
| W9 | Docling集成、多模板管理 | PDF深度解析、模板库 |
| W10 | 模板遵循度评分优化 | 评分算法调优 |

### Phase 4: 发布（第11-12周）

| 周次 | 任务 | 交付物 |
|-----|------|-------|
| W11 | 性能优化、错误处理 | 性能基准、健壮性提升 |
| W12 | 文档、测试、发布 | README、使用文档、v1.0 |

---

## 九、项目结构

```
group-meeting-ppt-agent/
├── README.md
├── requirements.txt
├── setup.py
│
├── src/
│   ├── __init__.py
│   ├── agent.py                  # 主入口
│   │
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── document_parser.py    # 通用文档解析
│   │   ├── template_extractor.py # 模板DNA提取
│   │   └── content_structurer.py # LLM内容结构化
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── planner.py
│   │   ├── generator.py
│   │   ├── refiner.py
│   │   └── validator.py
│   │
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── pptx_builder.py
│   │   ├── chart_generator.py
│   │   ├── style_lock.py
│   │   └── layout_engine.py
│   │
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── layout_validator.py
│   │   ├── compliance_checker.py
│   │   └── content_checker.py
│   │
│   └── templates/
│       └── default_academic.pptx
│
├── tests/
│   ├── test_parser.py
│   ├── test_template.py
│   ├── test_generator.py
│   └── test_validator.py
│
└── docs/
    ├── architecture.md
    ├── template-guide.md
    └── api-reference.md
```

---

## 十、风险与应对

| 风险 | 概率 | 影响 | 应对 |
|-----|------|------|------|
| 复杂模板解析失败 | 中 | 高 | 降级到基础样式提取 + 用户手动调整 |
| LLM结构化质量不稳定 | 中 | 中 | 多次采样 + 后处理规则保证统一结构 |
| 图表与模板风格不匹配 | 低 | 中 | 强制使用模板色板 + 人工审核点 |
| 大文件处理超时 | 低 | 低 | 流式处理 + 内容截断 + 进度反馈 |
| 用户对结果不满意 | 中 | 中 | 支持交互式逐页调整 + 大纲确认机制 |

---

## 附录：参考项目

| 项目 | 地址 |
|-----|------|
| ppt-master | https://github.com/hugohe3/ppt-master |
| MarkItDown | https://github.com/microsoft/markitdown |
| Docling | https://github.com/docling-project/docling |
| Auto-Slides | https://github.com/Westlake-AGI-Lab/Auto-Slides |
| pptx-generator | https://github.com/paul0728/pptx-generator |
