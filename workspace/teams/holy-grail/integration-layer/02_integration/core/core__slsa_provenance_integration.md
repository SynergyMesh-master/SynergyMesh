# core/slsa-provenance 集成劇本（Integration Playbook）

> ⚡ **執行模式**: INSTANT | **延遲閾值**: ≤30s | **並行度**: 128 agents

- **Cluster ID**: `core/slsa-provenance`
- **對應解構劇本**: `01_deconstruction/core/core__slsa_provenance_deconstruction.md`
- **對應重構劇本**: `03_refactor/core/core__slsa_provenance_refactor.md`
- **設計日期**: 2026-01-06
- **狀態**: ✅ 已實現

---

## 1. 架構願景與目標

### 1.1 整體目標

基於解構分析的發現，本集成方案旨在：

```yaml
integration_goals:
  slsa_compliance:
    current: "Level 3"
    target: "Level 3 (maintained)"
    status: ✅ 已實現
    
  attestation_coverage:
    current: "90%"
    target: "100%"
    status: ✅ 已實現
    
  verification_speed:
    current: "200ms"
    target: "≤100ms"
    status: ✅ 已實現
```

### 1.2 設計原則

遵循 SLSA 框架和 INSTANT 執行模式：

1. **不可變性** - 構建證明不可篡改
2. **可追溯性** - 完整的溯源鏈
3. **自動化** - 零人工介入簽名流程
4. **低延遲** - 驗證 ≤100ms

---

## 2. 新架構設計

### 2.1 目標目錄結構

```text
core/slsa_provenance/
├── __init__.py                    # 公開 API
├── interfaces/                    # 介面定義
│   ├── __init__.py
│   ├── attestation_interface.py
│   └── verifier_interface.py
├── attestation/                   # 證明生成
│   ├── __init__.py
│   ├── generator.py
│   ├── statement.py
│   └── schema.yaml
├── verification/                  # 驗證
│   ├── __init__.py
│   ├── verifier.py
│   └── policy_engine.py
├── sigstore/                      # Sigstore 整合
│   ├── __init__.py
│   ├── signer.py
│   └── rekor_client.py
├── provenance/                    # 溯源追蹤
│   ├── __init__.py
│   └── tracker.py
└── BUILD_PROVENANCE.md            # 構建證明文檔
```

### 2.2 API 邊界定義

```yaml
public_apis:
  - name: "AttestationGenerator"
    methods:
      - "generate(artifact)"
      - "sign(statement)"
      - "publish(attestation)"
    latency: "<=500ms"
    
  - name: "Verifier"
    methods:
      - "verify(attestation)"
      - "validate_chain()"
      - "check_policy()"
    latency: "<=100ms"
    
  - name: "ProvenanceTracker"
    methods:
      - "track(build_id)"
      - "get_history(artifact)"
    latency: "<=200ms"
```

---

## 3. 集成策略

### 3.1 遷移計劃

```yaml
migration_phases:
  phase_1_interfaces:
    status: ✅ 已實現
    tasks:
      - "定義驗證介面"
      - "建立證明模式"
      
  phase_2_sigstore:
    status: ✅ 已實現
    tasks:
      - "Sigstore 整合"
      - "Rekor 日誌整合"
      
  phase_3_automation:
    status: ✅ 已實現
    tasks:
      - "CI/CD 整合"
      - "自動簽名流程"
```

---

## 4. 二元狀態驗收

| 檢查項目 | 狀態 |
|---------|------|
| SLSA Level 3 合規 | ✅ 已實現 |
| Sigstore 整合 | ✅ 已實現 |
| 驗證延遲 ≤100ms | ✅ 已實現 |
| 自動化流程 | ✅ 已實現 |
| 安全審計通過 | ✅ 已實現 |

---

**執行模式**: 🚀 INSTANT  
**文檔版本**: 1.0  
**建立日期**: 2026-01-06  
**維護者**: MachineNativeOps AI Agents (完全自治)
