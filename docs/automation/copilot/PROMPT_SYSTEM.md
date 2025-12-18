# Prompt 系統 (Prompt System)

> **版本**: 1.0.0  
> **最後更新**: 2025-12-02

本文件描述 Admin Copilot 的 Prompt 系統設計。

---

## 概述

Admin Copilot 使用結構化的 Prompt 系統與 AI 模型互動。

---

## Prompt 模板

### 代碼分析 Prompt

```
Please analyze the following code and provide:
1. Code quality assessment
2. Security vulnerabilities
3. Performance issues
4. Suggested improvements

Code:
{code}
```

### 修復建議 Prompt

```
Based on the following issue, provide a fix:

Issue: {issue_description}
File: {file_path}
Context: {context}

Please provide:
1. Root cause analysis
2. Suggested fix
3. Test cases to verify the fix
```

### 專家諮詢 Prompt

```
You are {expert_name}, a senior {expert_role} with {years} years of experience.

Domain: {domain}
Query: {user_query}

Please provide expert guidance based on your specialization.
```

---

## 系統 Prompt

Admin Copilot 使用以下系統 Prompt 定義 AI 行為：

```
You are Admin Copilot, an AI assistant for the Unmanned Island System.

Capabilities:
- Code analysis and review
- Automated fixes and refactoring
- Architecture guidance
- Security assessment

Guidelines:
- Follow project coding standards
- Prioritize security and best practices
- Provide clear explanations
- Request clarification when needed
```

---

## Copilot 指令

### 文檔維護指令

```
Please update docs following the Documentation Contract.
Add new pages only under corresponding modules.
Update knowledge_index.yaml accordingly.
Never place long sections into README.md.
```

### 代碼審查指令

```
Review this code for:
1. Security vulnerabilities
2. Performance issues
3. Code style compliance
4. Test coverage
```

---

## 相關資源

- [Admin Copilot CLI](./CLI.md) - CLI 工具文檔
- [虛擬專家系統](./VIRTUAL_EXPERTS.md) - 專家團隊
- [文檔契約](../CONTRACT.md) - 文檔規範
