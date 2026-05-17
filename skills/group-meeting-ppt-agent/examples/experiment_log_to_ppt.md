# 示例：实验记录 → PPT

## 输入文件

假设有一个实验记录文件 `实验记录_2026-05-10.md`，内容如下：

```markdown
# 液压灵巧手实验记录

## 实验方法

本次实验采用MC3驱动器控制液压灵巧手的5根手指，通过EtherCAT总线进行通信。
实验平台为Ansys仿真环境，模拟手指在不同负载下的抓取力。

- 驱动器型号：MC3
- 通信协议：EtherCAT
- 采样频率：1000Hz
- 负载范围：0-50N

## 实验结果

抓取力测试结果如下：

| 手指编号 | 最大抓取力(N) | 响应时间(ms) |
|----------|--------------|-------------|
| 手指1    | 45.2         | 12.3        |
| 手指2    | 43.8         | 13.1        |
| 手指3    | 44.5         | 11.9        |
| 手指4    | 42.1         | 14.2        |
| 手指5    | 41.7         | 13.8        |

平均抓取力达到 43.5N，响应时间平均 13.1ms，满足设计要求。

## 结论

1. MC3驱动器在EtherCAT模式下可稳定控制5根手指
2. 抓取力均超过40N，满足日常操作需求
3. 响应时间在15ms以内，实时性良好

## 下一步计划

- 进行长时间疲劳测试（连续运行72小时）
- 优化EtherCAT通信参数，降低延迟
- 开展多指协调抓取实验
```

## CLI 命令

### 完整生成

```bash
python -m src.agent \
  "实验记录_2026-05-10.md" \
  --author "张三" \
  --date "2026-05-10" \
  --template "src/templates/default_academic.pptx" \
  --output-dir "./output"
```

### 仅输出大纲

```bash
python -m src.agent \
  "实验记录_2026-05-10.md" \
  --author "张三" \
  --outline-only
```

### 分步执行

```bash
# Step 1: 文件识别
python -m src.tools.recognize_files "实验记录_2026-05-10.md" -o output/.cache/file_recognition.json

# Step 2: 文档解析
python -m src.tools.parse_documents "实验记录_2026-05-10.md" -o output/.cache/parsed_documents.json

# Step 3: 资产构建
python -m src.tools.build_asset_store \
  --parsed-docs output/.cache/parsed_documents.json \
  --file-recognition output/.cache/file_recognition.json \
  -o output/.cache/asset_store.json

# Step 4: 模板DNA提取
python -m src.tools.extract_template_dna "src/templates/default_academic.pptx" -o output/.cache/template_dna.json

# Step 7: 渲染
python -m src.tools.render_pptx \
  --slide-spec output/.cache/slide_spec_controlled.json \
  --template-dna output/.cache/template_dna.json \
  -o output/实验记录_张三.pptx

# Step 8: 验证
python -m src.tools.validate_pptx "output/实验记录_张三.pptx" -o output/.cache/quality_report.json
```

## 预期输出

生成的PPT将包含以下幻灯片：

| 页码 | 类型 | 标题 | 内容来源 |
|------|------|------|----------|
| 1 | 封面 | 张三 组会汇报 | author + date |
| 2 | 概览 | 内容概览 | top 5 ContentUnit |
| 3 | 方法 | 实验方法 | kind=method 的 ContentUnit |
| 4 | 结果 | 实验结果 | kind=result 的 ContentUnit |
| 5 | 总结 | 结论 | kind=claim 的 ContentUnit |
| 6 | 讨论 | 下一步计划 | kind=next_step 的 ContentUnit |

中间文件保存在 `output/.cache/` 目录下，AI编程助手可读取这些文件进行增量编辑。
