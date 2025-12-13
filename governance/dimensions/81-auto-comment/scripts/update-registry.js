/**
 * =============================================================================
 * SynergyMesh Governance - Update Events Registry
 * 81-auto-comment: Update Registry Script
 * =============================================================================
 *
 * 功能：
 * - 將自動評論事件寫入 governance/index/events/registry.json
 * - 維護事件歷史記錄
 * - 更新統計資訊
 *
 * 使用方式：
 * node update-registry.js --event-id "auto-comment-xxx" --status "failure" --workflow "CI Pipeline" --commit "abc123"
 *
 * =============================================================================
 */

const fs = require("fs");
const path = require("path");

// =============================================================================
// CONFIGURATION
// =============================================================================

const REGISTRY_PATH = path.join(
  process.cwd(),
  "governance",
  "index",
  "events",
  "registry.json"
);

const EVENT_FILE_PATH = path.join(
  process.cwd(),
  "governance",
  "dimensions",
  "81-auto-comment",
  "output",
  "event.json"
);

// =============================================================================
// ARGUMENT PARSING
// =============================================================================

function parseArgs() {
  const args = process.argv.slice(2);
  const params = {
    eventId: `auto-comment-${Date.now()}`,
    status: "failure",
    workflow: "CI Pipeline",
    commit: "unknown-commit",
    branch: null,
    prNumber: null,
    autoFixed: false,
    errorType: null,
    fixType: null,
  };

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case "--event-id":
        params.eventId = args[++i] || params.eventId;
        break;
      case "--status":
        params.status = args[++i] || params.status;
        break;
      case "--workflow":
        params.workflow = args[++i] || params.workflow;
        break;
      case "--commit":
        params.commit = args[++i] || params.commit;
        break;
      case "--branch":
        params.branch = args[++i];
        break;
      case "--pr-number":
        params.prNumber = args[++i];
        break;
      case "--auto-fixed":
        params.autoFixed = args[++i] === "true";
        break;
      case "--error-type":
        params.errorType = args[++i];
        break;
      case "--fix-type":
        params.fixType = args[++i];
        break;
      case "--from-file":
        // 從事件檔案讀取
        if (fs.existsSync(EVENT_FILE_PATH)) {
          const eventData = JSON.parse(fs.readFileSync(EVENT_FILE_PATH, "utf-8"));
          Object.assign(params, {
            eventId: eventData.id || params.eventId,
            status: eventData.status || params.status,
            workflow: eventData.workflow || params.workflow,
            commit: eventData.commit || params.commit,
            autoFixed: eventData.auto_fixed || params.autoFixed,
            errorType: eventData.error_type || params.errorType,
            fixType: eventData.fix_type || params.fixType,
          });
        }
        break;
    }
  }

  return params;
}

// =============================================================================
// REGISTRY OPERATIONS
// =============================================================================

function loadRegistry() {
  if (fs.existsSync(REGISTRY_PATH)) {
    try {
      return JSON.parse(fs.readFileSync(REGISTRY_PATH, "utf-8"));
    } catch (err) {
      console.error("無法解析 registry.json，將建立新的檔案。");
    }
  }

  // 建立預設結構
  return {
    $schema: "../schemas/event-registry.schema.json",
    version: "1.0.0",
    timestamp: new Date().toISOString(),
    metadata: {
      name: "Governance Event Registry",
      description: "持久化事件索引 - 解決代理失憶問題",
      purpose: "讓所有代理啟動時都能讀取完整事件上下文",
      status: "production",
      ready: "immediate",
    },
    bootstrap_contract: {
      description: "入口協定 - 強制代理讀取事件",
      required_context: [
        "events/registry.json",
        "events/vector-index.json",
        "events/current-session.json",
      ],
      validation: {
        ci_gate: true,
        block_on_missing: true,
        error_message: "Agent must read events before execution",
      },
    },
    storage: {
      logs_path: "events/logs/",
      compressed_path: "events/compressed/",
      current_session: "events/current-session.json",
      retention: {
        hot: "7d",
        warm: "30d",
        cold: "365d",
      },
      compression: {
        enabled: true,
        threshold_events: 100,
        algorithm: "vectorize",
      },
    },
    event_dag: {
      description: "事件因果關係 DAG - 確保事件閉環",
      flow_patterns: [
        {
          id: "policy-flow",
          chain: [
            "policy.created",
            "policy.validated",
            "policy.enforced",
            "audit.logged",
          ],
          closes_at: "feedback.collected",
        },
        {
          id: "agent-flow",
          chain: ["agent.registered", "agent.deployed", "agent.monitored"],
          on_failure: ["healing.triggered", "healing.completed"],
          closes_at: "audit.logged",
        },
        {
          id: "decision-flow",
          chain: [
            "intent.received",
            "intent.mapped",
            "automation.started",
            "automation.completed",
          ],
          closes_at: "feedback.analyzed",
        },
        {
          id: "auto-comment-flow",
          chain: [
            "ci.failed",
            "auto-comment.triggered",
            "auto-comment.generated",
            "auto-comment.posted",
            "event.registered",
          ],
          on_auto_fix: [
            "auto-fix.triggered",
            "auto-fix.completed",
            "commit.created",
          ],
          closes_at: "feedback.collected",
          dimension: "81-auto-comment",
        },
      ],
    },
    events: [],
    files: [],
    statistics: {
      total_events: 0,
      total_files: 0,
      last_event_id: null,
      last_update: new Date().toISOString(),
      auto_comment_stats: {
        total_auto_comments: 0,
        total_auto_fixes: 0,
        auto_fix_success_rate: 0,
      },
    },
    shared_context: {
      enabled: true,
      scope: "all_agents",
      sync_interval: "10s",
      max_context_size: 10000,
    },
  };
}

function saveRegistry(registry) {
  // 確保目錄存在
  const registryDir = path.dirname(REGISTRY_PATH);
  if (!fs.existsSync(registryDir)) {
    fs.mkdirSync(registryDir, { recursive: true });
  }

  // 更新時間戳
  registry.timestamp = new Date().toISOString();

  // 寫入檔案
  fs.writeFileSync(REGISTRY_PATH, JSON.stringify(registry, null, 2), "utf-8");
  console.log(`✅ Registry 已更新: ${REGISTRY_PATH}`);
}

function addEvent(registry, params) {
  const newEvent = {
    id: params.eventId,
    type: "auto-comment",
    dimension: "81-auto-comment",
    workflow: params.workflow,
    commit: params.commit,
    branch: params.branch,
    pr_number: params.prNumber,
    status: params.status,
    auto_fixed: params.autoFixed,
    error_type: params.errorType,
    fix_type: params.fixType,
    timestamp: new Date().toISOString(),
    metadata: {
      generated_by: "81-auto-comment/scripts/update-registry.js",
      version: "1.0.0",
    },
  };

  // 確保 events 陣列存在
  if (!registry.events) {
    registry.events = [];
  }

  // 新增事件
  registry.events.push(newEvent);

  // 更新統計
  updateStatistics(registry, params);

  return newEvent;
}

function updateStatistics(registry, params) {
  if (!registry.statistics) {
    registry.statistics = {
      total_events: 0,
      total_files: 0,
      last_event_id: null,
      last_update: new Date().toISOString(),
      auto_comment_stats: {
        total_auto_comments: 0,
        total_auto_fixes: 0,
        auto_fix_success_rate: 0,
      },
    };
  }

  const stats = registry.statistics;
  stats.total_events = registry.events ? registry.events.length : 0;
  stats.last_event_id = params.eventId;
  stats.last_update = new Date().toISOString();

  // 更新 auto-comment 特定統計
  if (!stats.auto_comment_stats) {
    stats.auto_comment_stats = {
      total_auto_comments: 0,
      total_auto_fixes: 0,
      auto_fix_success_rate: 0,
    };
  }

  stats.auto_comment_stats.total_auto_comments++;

  if (params.autoFixed) {
    stats.auto_comment_stats.total_auto_fixes++;
  }

  // 計算成功率
  if (stats.auto_comment_stats.total_auto_comments > 0) {
    stats.auto_comment_stats.auto_fix_success_rate =
      stats.auto_comment_stats.total_auto_fixes /
      stats.auto_comment_stats.total_auto_comments;
  }
}

// =============================================================================
// MAIN FUNCTION
// =============================================================================

function main() {
  console.log("=== Update Events Registry (81-auto-comment) ===\n");

  // 解析參數
  const params = parseArgs();
  console.log("Event Parameters:", params);

  // 載入 registry
  const registry = loadRegistry();
  console.log(
    `\nRegistry 載入成功，現有 ${registry.events?.length || 0} 個事件`
  );

  // 新增事件
  const newEvent = addEvent(registry, params);
  console.log(`\n✅ 新增事件: ${newEvent.id}`);

  // 儲存 registry
  saveRegistry(registry);

  // 輸出結果
  console.log("\n=== 事件詳情 ===");
  console.log(JSON.stringify(newEvent, null, 2));

  console.log("\n=== 統計資訊 ===");
  console.log(JSON.stringify(registry.statistics, null, 2));

  console.log("\n=== 完成 ===");
}

// 執行
main();
