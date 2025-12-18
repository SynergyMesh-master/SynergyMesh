# 統一工具鏈

## 組成

- **Build**：Bazel（主要）、Pants（輔助 Python）
- **Package Registry**：內部 npm/pypi/crates/maven proxy
- **Testing**：Unified Test Runner（整合 Jest, Pytest, Go test）
- **Lint**：多語言風格統一規則庫

## Bazel 範例

```python
# WORKSPACE 中引用共用模組
load("@island_rules//:deps.bzl", "island_deps")
island_deps()
```

```python
# go_services/BUILD.bazel
go_binary(
    name = "api-gateway",
    srcs = glob(["*.go"]),
    deps = [
        "//shared/go/logging",
        "@com_github_gin_gonic_gin//:gin",
    ],
)
```

## 測試聚合

```bash
bazel test //...
```

或使用 CLI：

```bash
island-cli test:all
```

## 治理

- 所有工具鏈設定集中在 `tools/` + `config/dependencies.yaml`
- 版本鎖定 + 自動升級提報
- 透過 island-cli `toolchain:doctor` 檢查
