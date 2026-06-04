# Bid Document Analyzer

面向招标、采购、磋商、比选、入库、RFP/RFQ 文件的 Codex skill。

它的目标不是复述招标文件，而是把文件拆成能直接使用的交付物：客户能看懂的资料清单、客户可外发的招标文件深度分析，以及内部同事能用来判断和沟通的投标分析。

## 适用场景

- 整理投标资料清单
- 区分硬性资格、废标项、格式材料、得分材料
- 拆解评分标准和具体分值
- 分析报价、合同、付款、履约、知识产权等风险
- 从投标人角度分析利弊、投标过程和工程履约注意事项
- 排查限制性/禁止性条款、疑似定向或围标风险信号
- 生成客户可外发版 Word/HTML/PDF
- 生成内部销售/投标判断版 Word/HTML/PDF
- 将 HTML 交付物导出为 PDF、PNG 或 JPG

## 主要产出

| 产出 | 用途 |
| --- | --- |
| 客户版资料清单 | 可直接发给客户，重点是需要准备什么、缺了有什么后果 |
| 客户版深度分析 | 从投标人角度分析利弊、限制性条款、疑似定向/围标风险和履约注意事项 |
| 内部版判断卡 | 给销售、标书、项目同事看，判断能不能做、值不值得推进 |
| 评分拆解表 | 按原文逐项整理分值、证明材料、方案要求 |
| 风险与机会提示 | 提醒低价、履约、付款、二次比选、知识产权等风险 |
| HTML 导出工具 | 在无桌面服务器或 CI 环境中导出 PDF/PNG/JPG |
| 手机端客户版 | 客户版 HTML 按手机阅读优化；客户版 PDF 默认做紧凑表格版，避免长卡片流 |

## 安装

把仓库克隆到 Codex skills 目录：

```bash
git clone https://github.com/ehlengithub/bid-document-analyzer.git \
  ~/.codex/skills/bid-document-analyzer
```

如果目录已存在，先备份或删除旧目录后再克隆。

## 使用方式

在 Codex 中提供招标文件，并提出类似需求：

```text
用 bid-document-analyzer 处理这个招标文件，生成客户版资料清单、客户版深度分析和内部版投标判断卡，Word 和 HTML 都要。
```

也可以更具体：

```text
帮我拆一下这份磋商文件：哪些是废标项，哪些只是承诺函/盖章材料，评分标准每项多少分，也整理出来。
```

## 导出 HTML

脚本位置：

```bash
scripts/export_html_artifacts.py
```

示例：

```bash
python scripts/export_html_artifacts.py input.html --pdf output.pdf --png output.png
```

客户版 PDF 默认应做手机紧凑表格版：保留表格结构，压缩列数，避免 A4 小字和长卡片流。需要 A4 打印版时再显式指定：

```bash
python scripts/export_html_artifacts.py input.html --pdf print.pdf --pdf-layout a4
```

推荐服务端依赖：

```bash
pip install playwright
python -m playwright install chromium
```

脚本默认会优先尝试可用后端，适合无桌面服务器、容器和 CI 环境。

## 设计原则

- 只把原文明确写成资格、实质性、无效响应、废标/无效处理的内容标为硬门槛。
- 承诺函、声明函、截图、盖章材料不混同为客户实力门槛。
- 评分项必须写清具体分值和触发条件，不凭经验补分。
- 客户版不出现内部销售词。
- 客户版文字要自然、易懂、顺口，像资深投标顾问写给客户的简报；不能为了严谨写成模板腔或 AI 腔。
- 客户版 HTML/PDF 优先适配手机端阅读，正文和表格字号不能过小；PDF 要保留紧凑表格结构，不依赖横向拖动、A4 缩小阅读或长卡片流。
- 客户版深度分析要区分原文事实、风险信号和业务判断；没有直接证据时不作围标、串标或预设结果的确定性结论。
- 内部版可以写业务判断，但要和招标文件原文事实区分。
- 输出前必须做反幻觉检查，避免跨项目残留和模板误伤。

## 目录结构

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   └── tender-analysis-patterns.md
└── scripts/
    └── export_html_artifacts.py
```

## 说明

本 skill 用于辅助招投标文件拆解和交付物生成，不替代律师、招标代理或采购人的正式意见。涉及资格、废标、合同和付款等关键判断时，应以招标文件原文和采购人/代理答疑为准。
