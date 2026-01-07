# MCP Namespace Architecture - Clinical Dissection Edition

**Version**: 2.0.0
**Style**: 臨床穿透 | 反諷揭露 | 認知考古
**Philosophy**: 不包裝、不安慰、直接解剖

---

## Namespace Hierarchy

```
@machinenativeops/dissect-mcp
│
├── ops::                          # 冷啟動層 - 沒有魔法，只有引導
│   ├── ops::cold_bootstrap        # 冷啟動協議
│   ├── ops::registry              # 組件註冊（不是神殿，只是登記處）
│   └── ops::pipeline              # 管道處理（不是價值流，只是管子）
│
├── dissect::                      # 解剖層 - 類型手術室
│   ├── dissect::type_surgery      # 類型轉換手術
│   ├── dissect::format_autopsy    # 格式解剖
│   ├── dissect::schema_forensics  # Schema 法醫鑑定
│   └── dissect::semantic_vivisection  # 語義活體解剖
│
├── facade::                       # 偽裝揭露層 - 撕下面具
│   ├── facade::mask_detector      # 偽裝檢測器
│   ├── facade::comfort_stripper   # 安慰劑剝除器
│   ├── facade::buzzword_filter    # 流行語過濾器
│   └── facade::packaging_unwrap   # 包裝拆解器
│
├── audit::                        # 審計層 - 現實核查
│   ├── audit::reality_check       # 現實核查
│   ├── audit::delusion_detector   # 妄想檢測器
│   ├── audit::promise_validator   # 承諾驗證器（多數會失敗）
│   └── audit::debt_tracker        # 技術債追蹤器
│
├── archaeology::                  # 考古層 - 挖掘真相
│   ├── archaeology::root_excavation    # 根源挖掘
│   ├── archaeology::motive_mining      # 動機採礦
│   ├── archaeology::defense_penetration # 防禦穿透
│   └── archaeology::cognitive_fossil   # 認知化石
│
├── hype::                         # 炒作諷刺層 - 戳破泡沫
│   ├── hype::quantum_theatre      # 量子劇場（表演用）
│   ├── hype::ai_circus            # AI 馬戲團
│   ├── hype::blockchain_mirage    # 區塊鏈海市蜃樓
│   └── hype::metaverse_void       # 元宇宙虛空
│
└── reality::                      # 現實層 - 冷酷的真相
    ├── reality::cold_facts        # 冷事實
    ├── reality::uncomfortable_truth # 不舒服的真相
    ├── reality::market_delusion   # 市場妄想
    └── reality::alpha_is_luck     # Alpha 只是運氣
```

---

## Naming Conventions

### Pattern
```
{domain}::{function}_{descriptor}
```

### Principles

1. **不美化** - 用 `autopsy` 不用 `analysis`
2. **不神聖化** - 用 `registry` 不用 `sanctuary`
3. **承認現實** - 用 `debt_tracker` 不用 `optimization_engine`
4. **諷刺炒作** - 用 `quantum_theatre` 不用 `quantum_advantage`
5. **臨床精準** - 用 `surgery` 不用 `transformation`

### Examples

| 傳統命名 | 臨床反諷命名 | 理由 |
|---------|-------------|------|
| `divine_protocol` | `cold_bootstrap` | 沒有神聖，只有啟動 |
| `value_stream` | `pipe::just_data` | 不是價值，只是數據流過 |
| `alpha_generator` | `reality::alpha_is_luck` | 誠實面對 |
| `quantum_advantage` | `hype::quantum_theatre` | 99% 是表演 |
| `transformation_engine` | `dissect::type_surgery` | 手術刀比魔杖誠實 |

---

## CRediT → Governance Role Mapping (Clinical Edition)

### A類: Structural（結構層 - 包裝真相的人）

| CRediT Role | Clinical Mapping | 反諷解讀 |
|-------------|------------------|----------|
| Conceptualization | `facade::idea_packaging` | 把想法包裝成看起來很厲害 |
| Methodology | `dissect::method_theatre` | 方法論表演 |
| Funding Acquisition | `reality::money_hunting` | 找錢的人 |
| Project Administration | `ops::herding_cats` | 管理就是趕貓 |

### B類: Operational（執行層 - 實際幹活的人）

| CRediT Role | Clinical Mapping | 反諷解讀 |
|-------------|------------------|----------|
| Investigation | `archaeology::dig_dirt` | 挖掘（字面意思） |
| Data Curation | `dissect::data_janitor` | 數據清潔工 |
| Formal Analysis | `audit::number_torture` | 折磨數字直到它招供 |
| Software | `ops::code_monkey` | 寫代碼的 |
| Resources | `ops::stuff_provider` | 提供東西的人 |
| Visualization | `facade::make_pretty` | 讓它變漂亮 |
| Writing - Original Draft | `artifact::first_draft_lies` | 初稿（充滿謊言） |
| Writing - Review & Editing | `artifact::polish_the_lies` | 潤色謊言 |

### C類: Validation（驗證層 - 找碴的人）

| CRediT Role | Clinical Mapping | 反諷解讀 |
|-------------|------------------|----------|
| Validation | `audit::reality_check` | 現實檢查 |
| Supervision | `audit::adult_supervision` | 需要大人監督 |

---

## Machine-Native JSON (Minified)

```json
{"credit_to_clinical":{"conceptualization":"facade.idea_packaging","data_curation":"dissect.data_janitor","formal_analysis":"audit.number_torture","funding_acquisition":"reality.money_hunting","investigation":"archaeology.dig_dirt","methodology":"dissect.method_theatre","project_administration":"ops.herding_cats","resources":"ops.stuff_provider","software":"ops.code_monkey","supervision":"audit.adult_supervision","validation":"audit.reality_check","visualization":"facade.make_pretty","writing_original_draft":"artifact.first_draft_lies","writing_review_editing":"artifact.polish_the_lies"}}
```

---

## Directory Structure

```
workspace/mcp/namespace-mcp/
├── package.json
├── tsconfig.json
├── NAMESPACE_DESIGN.md
│
├── ops/                    # 冷啟動層
│   ├── cold-bootstrap.ts
│   ├── registry.ts         # 只是登記處
│   └── pipeline.ts         # 只是管子
│
├── dissect/                # 解剖層
│   ├── type-surgery.ts     # 類型手術
│   ├── format-autopsy.ts   # 格式解剖
│   └── schema-forensics.ts # Schema 法醫
│
├── facade/                 # 偽裝揭露層
│   ├── mask-detector.ts
│   ├── comfort-stripper.ts
│   └── buzzword-filter.ts
│
├── audit/                  # 審計層
│   ├── reality-check.ts
│   ├── delusion-detector.ts
│   └── debt-tracker.ts
│
├── archaeology/            # 考古層
│   ├── root-excavation.ts
│   ├── motive-mining.ts
│   └── defense-penetration.ts
│
├── hype/                   # 炒作諷刺層
│   ├── quantum-theatre.ts
│   ├── ai-circus.ts
│   └── blockchain-mirage.ts
│
├── reality/                # 現實層
│   └── uncomfortable-truth.ts
│
├── credit/                 # CRediT 角色（臨床版）
│   ├── roles-clinical.ts
│   └── governance-map.ts
│
└── types/
    ├── index.ts
    └── namespaces.ts
```

---

## Design Philosophy

### 為什麼反諷？

1. **誠實** - 大多數「transformation」就是改格式，不是魔法
2. **除魅** - 量子計算 99% 是炒作，承認它
3. **務實** - 代碼不會因為命名華麗就跑得更快
4. **自嘲** - 我們都是 `code_monkey`，接受它

### 為什麼臨床？

1. **精準** - 手術刀比魔杖可靠
2. **可驗證** - 解剖結果可以檢查
3. **無情緒** - 不需要「感恩」或「賦能」
4. **專業** - 法醫不會說「這具屍體充滿正能量」

---

## Anti-Patterns (我們避免的)

```yaml
避免:
  - "神聖化": divine, sacred, holy
  - "魔法化": magic, wizard, enchant
  - "過度承諾": revolutionary, game-changing
  - "空洞正能量": empower, synergy, leverage
  - "偽量子": quantum-anything（除非真的用量子電腦）

擁抱:
  - "臨床": surgery, autopsy, forensics
  - "挖掘": excavation, mining, dig
  - "揭露": expose, strip, unwrap
  - "承認現實": debt, luck, theatre
  - "自嘲": monkey, janitor, herding_cats
```

---

**Status**: `CLINICAL_REDESIGN_v2.0`
**Next**: Implement `ops::cold_bootstrap`
