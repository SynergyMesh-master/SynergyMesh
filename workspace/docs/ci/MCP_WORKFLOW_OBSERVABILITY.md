# MCP Workflow Observability Dashboard

> CI 可觀測性儀表板配置 - MCP Workflow Metrics

## 📊 Dashboard Overview

本文檔定義 MCP 相關 CI 工作流的成功率和延遲監控指標。

---

## 🎯 Key Metrics

### 1. Workflow Success Rate (工作流成功率)

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| `instant_execution_success_rate` | INSTANT 執行驗證成功率 | >= 95% | < 90% |
| `governance_validation_success_rate` | 治理驗證成功率 | >= 98% | < 95% |
| `mcp_server_health_rate` | MCP 伺服器健康率 | >= 99% | < 95% |

### 2. Latency Metrics (延遲指標)

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| `instant_validation_p50_latency` | INSTANT 驗證 P50 延遲 | <= 30s | > 60s |
| `instant_validation_p95_latency` | INSTANT 驗證 P95 延遲 | <= 60s | > 120s |
| `governance_check_latency` | 治理檢查延遲 | <= 10s | > 30s |
| `full_pipeline_latency` | 完整管線延遲 | <= 3min | > 5min |

### 3. Throughput Metrics (吞吐量指標)

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| `daily_validations` | 每日驗證次數 | >= 10 | < 5 |
| `concurrent_jobs` | 並行作業數 | 64-256 | < 64 |

---

## 📈 Dashboard Configuration

### GitHub Actions Workflow Metrics

```yaml
# Metrics collection configuration
metrics:
  workflow_runs:
    - workflow: instant-execution-validator.yml
      metrics:
        - name: success_rate
          type: gauge
          description: "INSTANT execution validation success rate"
          query: "sum(successful_runs) / sum(total_runs) * 100"
        - name: duration_seconds
          type: histogram
          description: "Workflow duration in seconds"
          buckets: [30, 60, 120, 180, 300]
    
    - workflow: governance.yml
      metrics:
        - name: success_rate
          type: gauge
          description: "Governance validation success rate"
        - name: duration_seconds
          type: histogram
          description: "Governance check duration"
          buckets: [5, 10, 30, 60]

# Alert rules
alerts:
  - name: instant_execution_failure_rate_high
    condition: instant_execution_success_rate < 90
    severity: critical
    message: "INSTANT execution validation success rate below 90%"
    
  - name: governance_validation_slow
    condition: governance_check_latency > 30
    severity: warning
    message: "Governance validation taking longer than 30 seconds"
    
  - name: pipeline_latency_critical
    condition: full_pipeline_latency > 300
    severity: critical
    message: "Full pipeline exceeds 5 minute threshold"
```

---

## 🔗 Related Workflows

| Workflow | Path | Purpose |
|----------|------|---------|
| Instant Execution Validator | `.github/workflows/instant-execution-validator.yml` | 驗證 INSTANT 執行標準 |
| Governance | `.github/workflows/governance.yml` | 治理框架驗證 |
| CI | `.github/workflows/ci.yml` | 主 CI 管線 |

---

## 📋 Implementation Status

### Current State

- [x] INSTANT execution validator workflow exists
- [x] Governance validation workflows configured
- [x] Governance validation scripts implemented
  - `vision-tracker.py` - INSTANT 執行標準驗證
  - `validate-autonomy.py` - 自治度驗證
  - `latency-monitor.py` - 延遲合規驗證
- [ ] Prometheus/Grafana dashboard (future)
- [ ] GitHub Actions metrics export (future)

### Recommended Next Steps

1. **短期（1-2 週）**
   - 啟用 GitHub Actions 成功/失敗通知
   - 在 PR 中顯示驗證結果摘要

2. **中期（2-4 週）**
   - 整合 Prometheus 指標收集
   - 建立 Grafana 儀表板

3. **長期（1-2 月）**
   - 實現自動化性能退化檢測
   - 建立歷史趨勢分析

---

## 📊 Sample Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MCP CI Observability Dashboard                   │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────┐  ┌───────────────────────────────┐│
│  │   Success Rate (24h)          │  │   P95 Latency (24h)           ││
│  │   ████████████████ 98.5%      │  │   ████████░░░░ 45s            ││
│  │   Target: >= 95%              │  │   Target: <= 60s              ││
│  └───────────────────────────────┘  └───────────────────────────────┘│
│  ┌───────────────────────────────┐  ┌───────────────────────────────┐│
│  │   Daily Validations           │  │   Concurrent Jobs             ││
│  │   ▂▄█▇▅▄▆█▇▅▃▂▄█ 142 runs    │  │   ████████████░░ 192 agents   ││
│  │   Target: >= 10               │  │   Target: 64-256              ││
│  └───────────────────────────────┘  └───────────────────────────────┘│
│  ┌──────────────────────────────────────────────────────────────────┐│
│  │   Workflow Status                                                ││
│  │   ✅ instant-execution-validator   SUCCESS   45s                 ││
│  │   ✅ governance                     SUCCESS   12s                 ││
│  │   ✅ ci                             SUCCESS   1m 23s              ││
│  └──────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Usage

### Running Governance Validators Locally

```bash
# Run vision tracker (INSTANT execution standards)
python workspace/src/governance/scripts/vision-tracker.py \
  --config workspace/mcp/pipelines/unified-pipeline-config.yaml \
  --verbose

# Run autonomy validator
python workspace/src/governance/scripts/validate-autonomy.py \
  --config workspace/mcp/pipelines/unified-pipeline-config.yaml \
  --verbose

# Run latency monitor
python workspace/src/governance/scripts/latency-monitor.py \
  --config workspace/mcp/pipelines/unified-pipeline-config.yaml \
  --verbose
```

### Output Example

```
======================================================================
Vision Tracker - INSTANT Execution Standard Validator
======================================================================

[1/3] Checking latency compliance...
✅ Latency compliance: PASSED

[2/3] Checking parallelism level...
✅ Parallelism level: PASSED

[3/3] Checking autonomy degree...
✅ Autonomy degree: PASSED

Score: 100/100

======================================================================

✅ VALIDATION PASSED
```

---

*Last Updated: 2026-01-06*
*Version: 1.0.0*
