# CI/CD 配置

## Pipeline 階段

1. **Lint & Test**：多語言 lint + 單元測試
2. **Build & Scan**：Bazel 建置、容器掃描、SLSA 策略
3. **Deploy**：Staging → Canary → Production
4. **Post Deploy**：健康檢查、復盤

## GitHub Actions 片段

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm install
      - run: npm run test:all
      - run: npm run build
```

## 品質閘門

- 測試覆蓋率 > 85%
- 高風險變更進入 L3/L4 審批
- SLSA Provenance 必須存在

## CLI 支援

```bash
island-cli ci status
island-cli ci rerun --job build
```
