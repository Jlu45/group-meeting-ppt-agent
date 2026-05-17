# 示例：进展报告 → PPT

## 输入文件

假设有一个进展报告文件 `周报_2026第20周.md`，内容如下：

```markdown
# 第20周进展报告

## 本周完成

1. 完成了液压灵巧手手指装配体的SolidWorks建模
2. 在Ansys中建立了手指的有限元仿真模型
3. 调试了MC3驱动器的EtherCAT通信，采样率稳定在1000Hz
4. 初步完成了5指独立控制程序的开发

## 实验结果

### 仿真结果

手指在50N负载下的最大应力为 78.3MPa，远低于材料的屈服强度 235MPa。
最大变形量为 0.32mm，满足设计要求（< 0.5mm）。

### 驱动器测试

| 测试项目 | 结果 | 是否通过 |
|----------|------|----------|
| 通信稳定性 | 连续运行48h无断连 | 通过 |
| 响应延迟 | 平均13.1ms | 通过 |
| 力矩输出 | 0-5Nm线性度99.2% | 通过 |
| 温升测试 | 连续运行后温升<15°C | 通过 |

## 遇到的问题

1. SolidWorks装配体中手指3和手指4存在轻微干涉，需调整关节角度范围
2. Ansys仿真收敛速度较慢，单个工况需要约2小时计算时间
3. EtherCAT从站偶发丢帧，怀疑与线缆长度有关

## 下一步计划

1. 修复手指3/4干涉问题，更新装配体模型
2. 优化Ansys网格划分，目标将计算时间缩短至1小时以内
3. 更换屏蔽线缆测试EtherCAT通信稳定性
4. 开始多指协调抓取的仿真验证
5. 准备中期汇报PPT
```

## CLI 命令

### 完整生成

```bash
python -m src.agent \
  "周报_2026第20周.md" \
  --author "王五" \
  --date "2026-05-17" \
  --template "src/templates/default_academic.pptx" \
  --output-dir "./output"
```

### 仅输出大纲

```bash
python -m src.agent \
  "周报_2026第20周.md" \
  --author "王五" \
  --outline-only
```

### 多文件合并

如果有多周的进展报告需要合并：

```bash
python -m src.agent \
  "周报_2026第18周.md" \
  "周报_2026第19周.md" \
  "周报_2026第20周.md" \
  --author "王五" \
  --date "2026-05-17" \
  --output-dir "./output"
```

### 修复已有PPT

如果生成的PPT存在验证问题：

```bash
python -m src.tools.repair_pptx \
  --pptx "output/王五组会汇报_20260517_143000.pptx" \
  --issues "output/.cache/quality_report.json" \
  --template-dna "output/.cache/template_dna.json" \
  -o "output/王五组会汇报_repaired.pptx"
```

## 预期输出

生成的PPT将包含以下幻灯片：

| 页码 | 类型 | 标题 | 内容来源 |
|------|------|------|----------|
| 1 | 封面 | 王五 组会汇报 | author + date |
| 2 | 概览 | 内容概览 | top 5 ContentUnit |
| 3 | 方法 | 本周完成 | kind=method 的 ContentUnit |
| 4 | 结果 | 实验结果 | kind=result 的 ContentUnit |
| 5 | 讨论 | 遇到的问题 | kind=limitation 的 ContentUnit |
| 6 | 讨论 | 下一步计划 | kind=next_step 的 ContentUnit |

### 文件识别结果

文件识别器将自动识别此文件：
- `content_type`: `weekly_report`
- `ppt_purpose`: `progress`
- `suggested_slide_types`: `["progress", "timeline", "next_step"]`
- `date`: `2026-05-17`（从文件名中提取）

### 中间文件

所有中间文件保存在 `output/.cache/` 目录：

```
output/.cache/
├── file_recognition.json      # Step 1: 文件识别结果
├── parsed_documents.json      # Step 2: 解析后的Markdown
├── asset_store.json           # Step 3: 语义资产库
├── template_dna.json          # Step 4: 模板DNA
├── slide_spec.json            # Step 5: 幻灯片规格
├── slide_spec_controlled.json # Step 6: 密度控制后的规格
└── quality_report.json        # Step 8: 质量报告
```

AI编程助手可以读取这些中间文件，对任意步骤的结果进行人工修改后重新执行后续步骤。
