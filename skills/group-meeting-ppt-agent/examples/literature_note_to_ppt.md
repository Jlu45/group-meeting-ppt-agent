# 示例：文献笔记 → PPT

## 输入文件

假设有一个文献笔记文件 `文献笔记_SoftRobotics.md`，内容如下：

```markdown
# 软体机器人手综述笔记

## 背景

软体机器人因其固有的柔顺性和安全性，在人机交互和精密操作领域展现出巨大潜力。
传统刚性机器人在非结构化环境中容易造成损伤，而软体机器人能够自适应地包络目标物体。

- 软体机器人研究起源于2000年代初期
- 主要驱动方式：气动、液压、形状记忆合金(SMA)、介电弹性体(DE)
- 应用场景：医疗辅助、食品处理、深海探测

## 相关工作

### 气动软体手

Harvard的Soft Robotics Toolkit提出了一种气动驱动的PneuNet结构，
通过气压变化实现手指弯曲。优点是结构简单、成本低，缺点是需要外部气源。

### 液压软体手

MIT的液压驱动方案使用不可压缩流体，提供了更高的力输出精度。
液压系统响应速度快，但密封要求高，系统复杂度较大。

### 混合驱动方案

近年来出现了刚柔耦合的混合驱动方案，结合了刚性骨架的力输出能力和
软体材料的自适应包络能力，代表工作包括Festo的Adaptive Gripper。

## 方法

本文提出的液压灵巧手采用以下设计方案：

1. 刚性骨架 + 软体指尖的混合结构
2. MC3微型液压驱动器，支持EtherCAT总线
3. 5指独立控制，每指3个自由度
4. 基于力反馈的闭环控制策略

## 结论

1. 混合驱动方案兼顾了力输出和柔顺性
2. MC3驱动器体积小、响应快，适合灵巧手应用
3. 闭环控制策略显著提高了抓取稳定性

## 下一步计划

- 对比不同驱动方案的能效比
- 探索基于深度学习的自适应抓取策略
- 开展临床场景验证
```

## CLI 命令

### 完整生成

```bash
python -m src.agent \
  "文献笔记_SoftRobotics.md" \
  --author "李四" \
  --date "2026-05-15" \
  --template "src/templates/default_academic.pptx" \
  --output-dir "./output"
```

### 仅输出大纲

```bash
python -m src.agent \
  "文献笔记_SoftRobotics.md" \
  --author "李四" \
  --outline-only
```

### 使用自定义模板

```bash
python -m src.agent \
  "文献笔记_SoftRobotics.md" \
  --author "李四" \
  --date "2026-05-15" \
  --template "my_template.pptx" \
  --output-dir "./output"
```

## 预期输出

生成的PPT将包含以下幻灯片：

| 页码 | 类型 | 标题 | 内容来源 |
|------|------|------|----------|
| 1 | 封面 | 李四 组会汇报 | author + date |
| 2 | 概览 | 内容概览 | top 5 ContentUnit |
| 3 | 背景 | 背景 | kind=background 的 ContentUnit |
| 4 | 相关工作 | 相关工作 | kind=background 的 ContentUnit |
| 5 | 方法 | 方法 | kind=method 的 ContentUnit |
| 6 | 总结 | 结论 | kind=claim 的 ContentUnit |
| 7 | 讨论 | 下一步计划 | kind=next_step 的 ContentUnit |

### 文件识别结果

文件识别器将自动识别此文件：
- `content_type`: `literature_note`
- `ppt_purpose`: `background_and_related_work`
- `suggested_slide_types`: `["background", "related_work", "literature"]`

### 质量报告示例

```
==================================================
          PPT 质量检测报告
==================================================

  幻灯片数量: 7
  综合评分:   92.5 / 100  [A]

--------------------------------------------------
  分项评分:
--------------------------------------------------
  L1 结构完整性:  100.0 / 100
  L2 布局合理性:   92.0 / 100
  L3 模板合规性:   88.0 / 100
  L4 内容完整性:   90.0 / 100
```
