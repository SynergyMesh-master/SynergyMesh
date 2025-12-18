#!/usr/bin/env python3
"""
深度解決方案生成器 (Deep Solution Generator)

當 CI 失敗時，分析失敗原因並生成兩個不同角度的深度解決方案。

方案一：快速修復 - 針對當前問題的直接解決方案
方案二：深度重構 - 從根本上解決問題並預防未來發生

環境變數：
    WORKFLOW_NAME: 失敗的工作流程名稱
    RUN_URL: CI 執行結果的 URL
    PR_NUMBER: 關聯的 PR 編號（可選）
    BRANCH: 分支名稱
    COMMIT_SHA: Commit SHA
    FAILURE_JOBS: 失敗的 Jobs JSON 字串

輸出（JSON 到 stdout）：
    {
        "root_cause_analysis": {...},
        "solutions": [
            {...},  // 方案一
            {...}   // 方案二
        ]
    }
"""

import json
import os
import sys
from typing import Any, Dict


def get_env(name: str, default: str = '') -> str:
    """獲取環境變數，帶有預設值。"""
    return os.environ.get(name, default)


def get_env_json(name: str, default: list) -> list:
    """從環境變數獲取 JSON，帶有預設值。"""
    value = get_env(name, '')
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def analyze_failure_type(workflow_name: str, failed_jobs: list) -> dict:
    """分析失敗類型並返回分類結果。"""
    workflow_lower = workflow_name.lower()
    
    # 失敗類型分類
    failure_types = {
        'build': False,
        'test': False,
        'docker': False,
        'security': False,
        'deployment': False,
        'lint': False,
        'integration': False,
        'unknown': False
    }
    
    # 根據工作流程名稱判斷
    if any(x in workflow_lower for x in ['build', 'compile', '構建']):
        failure_types['build'] = True
    if any(x in workflow_lower for x in ['test', 'spec', '測試']):
        failure_types['test'] = True
    if any(x in workflow_lower for x in ['docker', 'container', 'image']):
        failure_types['docker'] = True
    if any(x in workflow_lower for x in ['security', 'codeql', 'scan', '安全']):
        failure_types['security'] = True
    if any(x in workflow_lower for x in ['deploy', 'cd', '部署']):
        failure_types['deployment'] = True
    if any(x in workflow_lower for x in ['lint', 'eslint', 'format']):
        failure_types['lint'] = True
    if any(x in workflow_lower for x in ['integration', 'e2e', '整合']):
        failure_types['integration'] = True
    
    # 根據失敗的 jobs 進一步判斷
    for job in failed_jobs:
        job_name = job.get('name', '').lower()
        if any(x in job_name for x in ['build', 'compile']):
            failure_types['build'] = True
        if any(x in job_name for x in ['test', 'spec']):
            failure_types['test'] = True
        if any(x in job_name for x in ['docker', 'container']):
            failure_types['docker'] = True
        if any(x in job_name for x in ['security', 'scan']):
            failure_types['security'] = True
        if any(x in job_name for x in ['deploy']):
            failure_types['deployment'] = True
        if any(x in job_name for x in ['lint', 'format']):
            failure_types['lint'] = True
    
    # 如果沒有匹配任何類型
    if not any(failure_types.values()):
        failure_types['unknown'] = True
    
    return failure_types


def generate_root_cause_analysis(
    workflow_name: str,
    failed_jobs: list,
    failure_types: dict
) -> dict:
    """生成根本原因分析。"""
    active_types = [k for k, v in failure_types.items() if v]
    
    # 根據失敗類型生成分析
    analyses = {
        'build': {
            'summary': '構建過程失敗',
            'details': '''構建失敗通常由以下原因造成：
1. 依賴版本衝突或依賴無法解析
2. 語法錯誤或類型錯誤
3. 環境配置問題（如 Node.js 版本不匹配）
4. 磁盤空間不足
5. 編譯器/打包工具配置錯誤'''
        },
        'test': {
            'summary': '測試執行失敗',
            'details': '''測試失敗通常由以下原因造成：
1. 新增代碼破壞了現有測試
2. 測試環境配置與生產環境不一致
3. 異步測試超時
4. 測試數據問題或 Mock 配置錯誤
5. 依賴服務不可用'''
        },
        'docker': {
            'summary': 'Docker 構建或運行失敗',
            'details': '''Docker 相關失敗通常由以下原因造成：
1. Dockerfile 語法錯誤
2. 基礎鏡像版本問題或無法拉取
3. 多階段構建配置錯誤
4. 容器資源限制（記憶體/CPU）
5. 網路配置問題'''
        },
        'security': {
            'summary': '安全掃描發現問題',
            'details': '''安全掃描失敗通常由以下原因造成：
1. 存在已知的安全漏洞
2. 使用了不安全的依賴版本
3. 代碼中存在安全風險模式
4. 敏感資訊洩漏風險
5. 不符合安全最佳實踐'''
        },
        'deployment': {
            'summary': '部署過程失敗',
            'details': '''部署失敗通常由以下原因造成：
1. 環境變數配置錯誤
2. 服務依賴不可用
3. 權限不足
4. 網路連接問題
5. 資源配額不足'''
        },
        'lint': {
            'summary': '程式碼風格檢查失敗',
            'details': '''Lint 失敗通常由以下原因造成：
1. 程式碼風格不符合規範
2. ESLint/Prettier 配置衝突
3. 未使用的變數或導入
4. 類型定義問題
5. 格式化不一致'''
        },
        'integration': {
            'summary': '整合測試失敗',
            'details': '''整合測試失敗通常由以下原因造成：
1. 服務間通信問題
2. API 契約變更
3. 資料庫連接問題
4. 外部服務不可用
5. 環境配置不一致'''
        },
        'unknown': {
            'summary': '未知類型的 CI 失敗',
            'details': '''需要進一步分析 CI 日誌以確定具體原因。
建議步驟：
1. 查看完整的 CI 執行日誌
2. 檢查最近的代碼變更
3. 確認環境配置是否正確
4. 聯繫團隊成員協助分析'''
        }
    }
    
    # 合併多種失敗類型的分析
    summary_parts = []
    details_parts = []
    
    for failure_type in active_types:
        if failure_type in analyses:
            summary_parts.append(analyses[failure_type]['summary'])
            details_parts.append(f"### {analyses[failure_type]['summary']}\n\n{analyses[failure_type]['details']}")
    
    return {
        'summary': '、'.join(summary_parts) if summary_parts else '需要進一步分析',
        'details': '\n\n---\n\n'.join(details_parts) if details_parts else '請查看完整的 CI 日誌',
        'failure_types': active_types
    }


def generate_solution_1(failure_types: dict, workflow_name: str) -> dict:
    """生成方案一：快速修復。"""
    active_types = [k for k, v in failure_types.items() if v]
    primary_type = active_types[0] if active_types else 'unknown'
    
    solutions = {
        'build': {
            'title': '快速修復構建錯誤',
            'description': '直接修復導致構建失敗的問題，快速恢復 CI 正常運作',
            'steps': [
                '執行 `npm ci` 或 `npm install` 重新安裝依賴',
                '檢查 `package.json` 和 `package-lock.json` 是否同步',
                '確認 Node.js 版本與專案要求一致',
                '執行 `npm run build` 在本地驗證構建',
                '檢查編譯錯誤訊息並修復語法問題'
            ],
            'code_example': '''# 本地驗證步驟
npm ci
npm run build

# 如果遇到依賴問題
rm -rf node_modules package-lock.json
npm install
npm run build''',
            'code_language': 'bash',
            'expected_outcome': '構建成功，CI 恢復正常',
            'risk_level': '低',
            'implementation_time': '15-30 分鐘',
            'long_term_benefit': '一般'
        },
        'test': {
            'title': '修復失敗的測試',
            'description': '定位並修復導致測試失敗的具體問題',
            'steps': [
                '執行 `npm test` 在本地重現問題',
                '查看失敗測試的錯誤訊息',
                '檢查最近的代碼變更是否影響測試',
                '修復測試斷言或更新測試預期值',
                '確保所有測試在本地通過後再推送'
            ],
            'code_example': '''# 本地運行測試
npm test

# 運行特定測試檔案
npm test -- --testPathPattern="failing-test"

# 查看測試覆蓋率
npm test -- --coverage''',
            'code_language': 'bash',
            'expected_outcome': '所有測試通過',
            'risk_level': '低',
            'implementation_time': '30-60 分鐘',
            'long_term_benefit': '一般'
        },
        'docker': {
            'title': '修復 Docker 構建問題',
            'description': '解決 Docker 映像構建或容器運行的問題',
            'steps': [
                '執行 `docker-compose build --no-cache` 重新構建',
                '檢查 Dockerfile 語法和基礎映像版本',
                '確認多階段構建的依賴正確複製',
                '檢查容器資源限制配置',
                '驗證網路配置和端口映射'
            ],
            'code_example': '''# 重新構建 Docker 映像
docker-compose build --no-cache --progress=plain

# 檢查映像
docker images

# 運行並查看日誌
docker-compose up --force-recreate''',
            'code_language': 'bash',
            'expected_outcome': 'Docker 映像成功構建並運行',
            'risk_level': '低',
            'implementation_time': '20-40 分鐘',
            'long_term_benefit': '一般'
        },
        'security': {
            'title': '修復安全漏洞',
            'description': '更新有安全問題的依賴或修復代碼中的安全風險',
            'steps': [
                '執行 `npm audit` 查看安全報告',
                '使用 `npm audit fix` 自動修復可修復的漏洞',
                '手動更新需要重大版本升級的依賴',
                '檢查並修復代碼中的安全風險',
                '重新運行安全掃描確認修復'
            ],
            'code_example': '''# 查看安全報告
npm audit

# 自動修復
npm audit fix

# 強制修復（可能有破壞性變更）
npm audit fix --force

# 更新特定依賴
npm update <package-name>''',
            'code_language': 'bash',
            'expected_outcome': '安全掃描通過',
            'risk_level': '中',
            'implementation_time': '30-60 分鐘',
            'long_term_benefit': '高'
        },
        'deployment': {
            'title': '修復部署配置',
            'description': '解決部署過程中的配置或環境問題',
            'steps': [
                '檢查環境變數配置是否正確',
                '確認服務依賴（資料庫、快取等）可用',
                '驗證部署權限和認證配置',
                '檢查網路連接和防火牆規則',
                '查看部署日誌定位具體錯誤'
            ],
            'code_example': '''# 檢查環境變數
env | grep -E "(NODE_ENV|DATABASE|API)"

# 測試服務連接
curl -v http://service-endpoint/health

# 驗證認證
echo $DEPLOY_TOKEN | head -c 10''',
            'code_language': 'bash',
            'expected_outcome': '部署成功完成',
            'risk_level': '中',
            'implementation_time': '30-60 分鐘',
            'long_term_benefit': '一般'
        },
        'lint': {
            'title': '修復程式碼風格問題',
            'description': '自動或手動修復程式碼風格問題',
            'steps': [
                '執行 `npm run lint` 查看所有問題',
                '使用 `npm run lint -- --fix` 自動修復',
                '手動修復無法自動修復的問題',
                '執行 `npm run format` 統一格式',
                '確保所有 lint 規則通過'
            ],
            'code_example': '''# 查看 lint 問題
npm run lint

# 自動修復
npm run lint -- --fix

# 格式化代碼
npm run format

# 或使用 Prettier
npx prettier --write "src/**/*.{ts,js}"''',
            'code_language': 'bash',
            'expected_outcome': 'Lint 檢查通過',
            'risk_level': '低',
            'implementation_time': '10-20 分鐘',
            'long_term_benefit': '一般'
        },
        'integration': {
            'title': '修復整合測試問題',
            'description': '解決服務間整合測試的失敗',
            'steps': [
                '確認所有相依服務正在運行',
                '檢查 API 契約是否有變更',
                '驗證測試環境配置',
                '檢查資料庫連接和測試數據',
                '重新運行整合測試'
            ],
            'code_example': '''# 啟動相依服務
docker-compose up -d db redis

# 運行整合測試
npm run test:integration

# 查看服務日誌
docker-compose logs -f''',
            'code_language': 'bash',
            'expected_outcome': '整合測試通過',
            'risk_level': '中',
            'implementation_time': '30-60 分鐘',
            'long_term_benefit': '一般'
        },
        'unknown': {
            'title': '通用問題排查',
            'description': '進行系統性的問題排查',
            'steps': [
                '仔細閱讀 CI 完整日誌',
                '對比成功和失敗的執行結果',
                '檢查最近的代碼變更',
                '在本地重現問題',
                '聯繫團隊成員協助分析'
            ],
            'code_example': '''# 查看本地環境
bash scripts/check-env.sh

# 運行完整 CI 流程
npm ci && npm run lint && npm run build && npm test''',
            'code_language': 'bash',
            'expected_outcome': '定位並解決問題',
            'risk_level': '中',
            'implementation_time': '依問題複雜度而定',
            'long_term_benefit': '一般'
        }
    }
    
    return solutions.get(primary_type, solutions['unknown'])


def generate_solution_2(failure_types: dict, workflow_name: str) -> dict:
    """生成方案二：深度重構。"""
    active_types = [k for k, v in failure_types.items() if v]
    primary_type = active_types[0] if active_types else 'unknown'
    
    solutions = {
        'build': {
            'title': '構建系統優化',
            'description': '重構構建配置，建立更穩健的構建流程',
            'steps': [
                '審查並更新 tsconfig.json / webpack 配置',
                '建立依賴版本鎖定策略',
                '實施漸進式構建（incremental build）',
                '添加構建快取機制',
                '建立構建健康檢查腳本'
            ],
            'code_example': '''// tsconfig.json 優化
{
  "compilerOptions": {
    "incremental": true,
    "tsBuildInfoFile": "./buildcache/tsbuildinfo",
    "strict": true
  }
}

// package.json 構建腳本
{
  "scripts": {
    "build": "tsc -b",
    "build:clean": "rm -rf dist && npm run build",
    "prebuild": "npm run lint"
  }
}''',
            'code_language': 'json',
            'expected_outcome': '構建更快、更穩定，問題更容易排查',
            'risk_level': '中',
            'implementation_time': '2-4 小時',
            'long_term_benefit': '高'
        },
        'test': {
            'title': '測試架構改進',
            'description': '建立更完善的測試體系，提高測試可靠性',
            'steps': [
                '建立測試金字塔：單元、整合、E2E 測試分層',
                '實施測試隔離，避免測試間相互影響',
                '建立測試數據工廠（Test Data Factory）',
                '添加測試覆蓋率門檻',
                '建立測試失敗自動重試機制'
            ],
            'code_example': '''// jest.config.js 優化
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80
    }
  },
  // 失敗重試
  retry: 2,
  // 測試超時
  testTimeout: 30000
};''',
            'code_language': 'javascript',
            'expected_outcome': '測試更穩定可靠，覆蓋率提高',
            'risk_level': '中',
            'implementation_time': '4-8 小時',
            'long_term_benefit': '高'
        },
        'docker': {
            'title': 'Docker 構建優化',
            'description': '優化 Docker 構建流程，提高效率和可靠性',
            'steps': [
                '實施多階段構建減少映像大小',
                '建立構建快取策略',
                '使用 .dockerignore 排除不必要檔案',
                '實施健康檢查（healthcheck）',
                '建立映像漏洞掃描流程'
            ],
            'code_example': '''# 優化的 Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:18-alpine AS runner
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .

HEALTHCHECK --interval=30s --timeout=3s \\
  CMD curl -f http://localhost:3000/health || exit 1

USER node
CMD ["node", "dist/server.js"]''',
            'code_language': 'dockerfile',
            'expected_outcome': '構建更快，映像更小更安全',
            'risk_level': '中',
            'implementation_time': '2-4 小時',
            'long_term_benefit': '高'
        },
        'security': {
            'title': '安全防護體系建設',
            'description': '建立完善的安全掃描和漏洞管理流程',
            'steps': [
                '建立依賴自動更新機制（Dependabot/Renovate）',
                '實施安全掃描門檻策略',
                '建立安全編碼規範和審查流程',
                '實施密鑰和敏感資訊管理',
                '建立安全事件響應流程'
            ],
            'code_example': '''# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    groups:
      security:
        applies-to: security-updates
        patterns:
          - "*"''',
            'code_language': 'yaml',
            'expected_outcome': '主動防護安全風險，快速響應漏洞',
            'risk_level': '低',
            'implementation_time': '4-8 小時',
            'long_term_benefit': '高'
        },
        'deployment': {
            'title': '部署流程現代化',
            'description': '建立更安全、可靠的部署流程',
            'steps': [
                '實施藍綠部署或金絲雀部署',
                '建立自動回滾機制',
                '實施配置即代碼（IaC）',
                '建立部署前後健康檢查',
                '實施部署審計和追蹤'
            ],
            'code_example': '''# 金絲雀部署配置
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: app-rollout
spec:
  strategy:
    canary:
      steps:
        - setWeight: 5
        - pause: {duration: 5m}
        - setWeight: 20
        - pause: {duration: 5m}
        - setWeight: 50
        - pause: {duration: 5m}''',
            'code_language': 'yaml',
            'expected_outcome': '部署更安全，問題可快速回滾',
            'risk_level': '高',
            'implementation_time': '8-16 小時',
            'long_term_benefit': '高'
        },
        'lint': {
            'title': '程式碼品質體系建設',
            'description': '建立統一的程式碼風格和品質標準',
            'steps': [
                '統一 ESLint/Prettier 配置',
                '實施 pre-commit hooks',
                '建立程式碼審查清單',
                '實施程式碼品質門檻',
                '建立技術債務追蹤機制'
            ],
            'code_example': '''// .eslintrc.js
module.exports = {
  extends: [
    'eslint:recommended',
    '@typescript-eslint/recommended',
    'prettier'
  ],
  rules: {
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/explicit-function-return-type': 'warn'
  }
};

// .husky/pre-commit
npm run lint-staged''',
            'code_language': 'javascript',
            'expected_outcome': '程式碼品質一致，減少風格爭議',
            'risk_level': '低',
            'implementation_time': '2-4 小時',
            'long_term_benefit': '高'
        },
        'integration': {
            'title': '整合測試環境改進',
            'description': '建立可靠的整合測試環境和流程',
            'steps': [
                '建立隔離的測試環境',
                '實施服務虛擬化（Service Virtualization）',
                '建立測試數據管理策略',
                '實施契約測試（Contract Testing）',
                '建立整合測試監控和報告'
            ],
            'code_example': '''// 契約測試範例 (Pact)
describe('User API Contract', () => {
  it('should return user by id', async () => {
    await provider.addInteraction({
      state: 'user exists',
      uponReceiving: 'a request for user',
      withRequest: {
        method: 'GET',
        path: '/users/1'
      },
      willRespondWith: {
        status: 200,
        body: {
          id: like(1),
          name: like('John')
        }
      }
    });
  });
});''',
            'code_language': 'typescript',
            'expected_outcome': '整合測試更穩定，服務契約有保障',
            'risk_level': '中',
            'implementation_time': '8-16 小時',
            'long_term_benefit': '高'
        },
        'unknown': {
            'title': 'CI/CD 流程現代化',
            'description': '全面審視並優化 CI/CD 流程',
            'steps': [
                '審計現有 CI/CD 流程',
                '建立失敗分析和監控系統',
                '實施 CI/CD 最佳實踐',
                '建立文檔和知識庫',
                '建立持續改進機制'
            ],
            'code_example': '''# CI 健康監控工作流程
name: CI Health Monitor
on:
  schedule:
    - cron: '0 */6 * * *'
jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - name: Check CI Success Rate
        run: |
          # 分析最近 100 次 CI 執行
          echo "Analyzing CI health..."''',
            'code_language': 'yaml',
            'expected_outcome': 'CI/CD 流程更高效、更可靠',
            'risk_level': '中',
            'implementation_time': '依範圍而定',
            'long_term_benefit': '高'
        }
    }
    
    return solutions.get(primary_type, solutions['unknown'])


def generate_solutions() -> Dict[str, Any]:
    """主函數：生成完整的解決方案報告。"""
    # 獲取環境變數
    workflow_name = get_env('WORKFLOW_NAME', 'Unknown Workflow')
    run_url = get_env('RUN_URL', '')
    pr_number = get_env('PR_NUMBER', '')
    branch = get_env('BRANCH', '')
    commit_sha = get_env('COMMIT_SHA', '')
    failed_jobs = get_env_json('FAILURE_JOBS', [])
    failure_type_override = get_env('FAILURE_TYPE', '')
    
    # 分析失敗類型
    failure_types = analyze_failure_type(workflow_name, failed_jobs)
    
    # 如果有指定的失敗類型（手動觸發），則覆蓋自動偵測的類型
    if failure_type_override and failure_type_override != 'auto':
        # 重置所有類型為 False
        failure_types = {k: False for k in failure_types}
        # 設置指定的類型為 True
        if failure_type_override in failure_types:
            failure_types[failure_type_override] = True
        else:
            # 記錄警告：未知的失敗類型
            print(f"警告：未知的失敗類型 '{failure_type_override}'，使用 'unknown' 類型", 
                  file=sys.stderr)
            failure_types['unknown'] = True
    
    # 生成根本原因分析
    root_cause = generate_root_cause_analysis(workflow_name, failed_jobs, failure_types)
    
    # 生成兩個解決方案
    solution_1 = generate_solution_1(failure_types, workflow_name)
    solution_2 = generate_solution_2(failure_types, workflow_name)
    
    return {
        'root_cause_analysis': root_cause,
        'solutions': [solution_1, solution_2],
        'metadata': {
            'workflow_name': workflow_name,
            'run_url': run_url,
            'pr_number': pr_number,
            'branch': branch,
            'commit_sha': commit_sha,
            'failure_types': failure_types,
            'failure_type_override': failure_type_override
        }
    }


def main() -> int:
    """程式入口點。"""
    try:
        result = generate_solutions()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except Exception as e:
        # 發生錯誤時輸出預設解決方案
        error_result = {
            'root_cause_analysis': {
                'summary': '分析過程發生錯誤',
                'details': f'錯誤訊息：{str(e)}\n請查看完整的 CI 日誌以獲取更多資訊。'
            },
            'solutions': [
                {
                    'title': '查看 CI 日誌',
                    'description': '請查看完整的 CI 執行日誌以了解具體錯誤',
                    'steps': [
                        '點擊 CI 執行結果連結',
                        '查看失敗的 Job 日誌',
                        '分析錯誤訊息',
                        '根據錯誤訊息進行修復'
                    ],
                    'expected_outcome': '定位問題原因',
                    'risk_level': '低',
                    'implementation_time': '視問題而定',
                    'long_term_benefit': '一般'
                },
                {
                    'title': '聯繫團隊協助',
                    'description': '如果無法自行解決，請聯繫團隊成員協助',
                    'steps': [
                        '在 Issue 或 PR 中描述問題',
                        '提供錯誤日誌截圖',
                        '說明已嘗試的解決方案',
                        '請求團隊協助'
                    ],
                    'expected_outcome': '獲得協助解決問題',
                    'risk_level': '低',
                    'implementation_time': '視協助回應而定',
                    'long_term_benefit': '高'
                }
            ],
            'error': str(e)
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False))
        return 0


if __name__ == '__main__':
    sys.exit(main())
