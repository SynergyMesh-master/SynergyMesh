# 安裝指南

## 系統需求

- Linux / macOS / Windows (WSL2)
- Node.js 20+
- Python 3.11+
- Rust 1.75+
- Go 1.21+
- Docker 24+（建議）

## 快速安裝

```bash
curl -fsSL https://island-ai.dev/install.sh | bash
```

或使用 npm：

```bash
npm install -g @island-ai/cli
```

## 手動部署

1. Clone 倉庫
2. `npm install`
3. `npm run bootstrap`（安裝多語言依賴）
4. `npm run build`
5. `npm run dev`

## 驗證

```bash
island-cli status
island-cli health --report
```
