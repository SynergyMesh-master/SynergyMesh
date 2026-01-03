# 🏝️ Language Governance Dashboard - Implementation Guide

> **Complete implementation of the Language Governance Dashboard for Unmanned Island System**

---

## 📋 Overview

This document describes the implementation of a comprehensive Language Governance Dashboard that provides real-time visualization and monitoring of language policy compliance across the Unmanned Island System.

### Features Implemented

✅ **Web Dashboard** - React/TypeScript frontend with modern UI  
✅ **API Backend** - FastAPI endpoint integrated into existing service  
✅ **Mermaid Diagrams** - Visual language layer architecture  
✅ **Sankey Diagram** - Dynamic language violation flow visualization  
✅ **Hotspot Heatmap** - Interactive violation intensity visualization  
✅ **Migration Flow Model** - Cluster-to-cluster language migration tracking  
✅ **Real-time Metrics** - Health scores, violations, security findings  
✅ **History Tracking** - Timeline of language governance events  
✅ **CI Integration** - Automated data updates via GitHub Actions  
✅ **Living Knowledge Base** - Auto-updating governance reports

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Language Governance System                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Frontend   │    │   Backend    │    │  CI/CD       │ │
│  │   (React)    │◄───┤  (FastAPI)   │◄───┤  (Actions)   │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                    │         │
│         │                    │                    │         │
│         ▼                    ▼                    ▼         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  Mermaid     │    │  Governance  │    │  Semgrep     │ │
│  │  Diagrams    │    │  Reports     │    │  Scanner     │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure

```
Unmanned-Island/
├── apps/web/
│   ├── src/
│   │   ├── pages/
│   │   │   └── LanguageGovernance.tsx        # Dashboard page
│   │   └── components/
│   │       ├── Mermaid.tsx                    # Mermaid component
│   │       └── SankeyDiagram.tsx              # Sankey diagram component
│   └── services/
│       ├── api.py                             # FastAPI with governance endpoint
│       └── api/
│           └── language_governance.py         # Standalone API service
├── tools/
│   └── generate-sankey-data.py                # Sankey data generator
├── governance/
│   ├── language-governance-report.md          # Main governance report
│   ├── semgrep-report.json                    # Security findings
│   └── sankey-data.json                       # Sankey diagram data
├── knowledge/
│   └── language-history.yaml                  # Event history
├── docs/
│   ├── KNOWLEDGE_HEALTH.md                    # Health score report
│   └── LANGUAGE_GOVERNANCE_IMPLEMENTATION.md  # This file
└── .github/workflows/
    └── language-governance-dashboard.yml      # CI automation
```

---

## 🎨 Frontend Implementation

### Dashboard Page (`LanguageGovernance.tsx`)

The dashboard provides:

1. **Health Score Overview**
   - Overall score (0-100)
   - Total violations
   - Security findings
   - Fix success rate

2. **Language Layer Model** (Mermaid)
   - Visual representation of language layers
   - L0-L5 architecture display

3. **Sankey Diagram** - Language Violation Flow
   - Visualizes: Source Layer → Violation Type → Fix Target
   - Shows most common violations and fix actions
   - Dynamic data from governance reports
   - Interactive flow visualization

4. **Violations Table**
   - File paths
   - Severity levels
   - Layer information
   - Issue descriptions

5. **Security Issues** (Semgrep)
   - Security findings
   - Vulnerability details
   - Severity classifications

6. **Activity Timeline**
   - Recent events
   - Fix history
   - Scan results

### Mermaid Component

Custom React component for rendering Mermaid diagrams with:

- Dark theme support
- Auto-rendering
- Responsive design

### Sankey Diagram Component

Interactive Sankey diagram showing language violation flows:

- **Purpose**: Visualizes the path from source layer through violation type to
  fix target
=======

- **Purpose**: Visualizes the path from source layer through violation type to fix target

>>>>>>> origin/copilot/sub-pr-402

- **Data Flow**: `Source Layer → Language → Violation Type → Fix Target`
- **Features**:
  - Dynamic data generation from governance reports
  - Flow statistics (total paths, most common violations, top fix actions)
  - Color-coded flows for easy identification
  - Responsive and scrollable design

**Example Flow**:

```
L5: Applications → JavaScript → Policy Violation → Rewrite to TypeScript
L1: Core Engine → Python → Type Safety → Add Type Hints
L4: Services → C++ → Layer Violation → Move to L0: Hardware
```

The Sankey diagram is automatically generated by `tools/generate-sankey-data.py`
which:

=======
The Sankey diagram is automatically generated by `tools/generate-sankey-data.py` which:

>>>>>>> origin/copilot/sub-pr-402

- Parses the governance report for violations
- Extracts source layer, language, and violation type
- Determines appropriate fix targets
- Aggregates duplicate flows
- Outputs `governance/sankey-data.json`

### Hotspot Heatmap Component

Interactive treemap visualization showing violation concentration:

- **Purpose**: Identifies files and directories with highest violation density
- **Visualization**: Color-coded blocks sized by violation score
- **Features**:
  - Heat intensity scoring algorithm
  - Critical (🔴 70-100), High (🟠 40-69), Moderate (🟡 1-39) color coding
  - Statistics: total hotspots, critical count, max intensity, hottest layer
  - Top 5 hotspots list with scores

**Hotspot Score Algorithm**:

```
Score = (ForbiddenLanguage × 5) + 
        (CrossLayerViolation × 3) + 
        (SecurityIssues × 2) + 
        (RepeatedViolations × 4)
```

**Example Hotspots**:

- `services/gateway/router.cpp` - Score: 90 (Critical - C++ in Services layer)
- `automation/scripts/config.lua` - Score: 55 (High - Lua forbidden)
- `apps/web/src/legacy-code.js` - Score: 45 (High - JS in TS project)
- `core/engine/utils.py` - Score: 20 (Moderate - Type safety)

The hotspot heatmap is automatically generated by
`tools/generate-hotspot-heatmap.py` which:

=======
The hotspot heatmap is automatically generated by `tools/generate-hotspot-heatmap.py` which:

>>>>>>> origin/copilot/sub-pr-402

- Parses governance report, semgrep findings, and violation history
- Calculates intensity scores using the hotspot algorithm
- Identifies most problematic files and layers
- Outputs `governance/hotspot-data.json` and `docs/HOTSPOT_HEATMAP.md`

### Migration Flow Model Component

Cluster-to-cluster language migration visualization:

- **Purpose**: Track language migration patterns between directory clusters
- **Visualization**: Sankey diagram showing migration flows with Mermaid
- **Features**:
  - Historical migrations (completed changes marked with ✓)
  - Suggested migrations (based on current violations marked with →)
  - Statistics: total migrations, most common source/target
  - Top migration paths table

**Migration Edge Structure**:

```
source: "<cluster>:<language>" → target: "<cluster>:<language>"
Examples:
- services:cpp → automation/autonomous:cpp (move C++ to correct layer)
- apps/web:javascript → apps/web:typescript (rewrite to TS)
- automation:lua → removed:removed (remove forbidden language)
```

**Migration Types**:

- **history**: Completed migrations from `language-history.yaml` events
- **suggested**: Recommended migrations derived from current violations

**Example Flows**:

- `services:cpp → automation/autonomous:cpp` (3 suggested) - C++ belongs in
  autonomous layer
=======

- `services:cpp → automation/autonomous:cpp` (3 suggested) - C++ belongs in autonomous layer

>>>>>>> origin/copilot/sub-pr-402

- `apps/web:javascript → apps/web:typescript` (2 suggested) - Rewrite JS to TS
- `core/engine:typescript → core/engine:typescript` (2 history) - Completed improvements
- `governance:typescript → core:typescript` (1 suggested) - Move TS from governance to core
- `automation:lua → removed:removed` (1 suggested) - Remove forbidden Lua

The migration flow model is automatically generated by
`tools/generate-migration-flow.py` which:

=======
The migration flow model is automatically generated by `tools/generate-migration-flow.py` which:

>>>>>>> origin/copilot/sub-pr-402

- Parses governance report for current violations
- Reads `language-history.yaml` for completed migrations
- Determines clusters from file paths (e.g., `core/`, `services/`, `automation/`)
- Identifies languages from file extensions
- Suggests target clusters/languages based on violation types
- Outputs `governance/migration-flow.json` and `docs/MIGRATION_FLOW.md`

---

## 🔌 Backend API

### Endpoint: `/api/v1/language-governance`

**Method:** GET  
**Returns:** JSON with governance data

**Response Schema:**

```json
{
  "healthScore": 85,
  "violations": [...],
  "semgrep": {
    "errors": 0,
    "results": [...]
  },
  "history": [...],
  "generatedAt": "2025-12-06T15:20:00Z",
  "metrics": {
    "totalViolations": 2,
    "securityFindings": 1,
    "architectureCompliance": 92,
    "fixSuccessRate": 87
  }
}
```

### Data Sources

The API reads from:

- `governance/language-governance-report.md` - Violations
- `governance/semgrep-report.json` - Security findings
- `knowledge/language-history.yaml` - Event history
- `docs/KNOWLEDGE_HEALTH.md` - Health score

---

## 🤖 CI/CD Automation

### Workflow: `language-governance-dashboard.yml`

**Triggers:**

- Push to main/develop
- Pull requests
- Daily schedule (00:00 UTC)
- Manual dispatch

**Steps:**

1. **Language Scan**
   - Count files by language
   - Generate distribution report

2. **Security Scan**
   - Run Semgrep (if available)
   - Generate security report

3. **Health Calculation**
   - Calculate health score (0-100)
   - Determine grade (A-F)
   - Update health report

4. **Report Generation**
   - Update governance report
   - Update history with new event

5. **Data Distribution**
   - Copy data to web app
   - Commit changes (if any)

---

## 📊 Language Layer Model

The system enforces language policies across 6 layers:

| Layer | Name | Allowed Languages | Purpose |
|-------|------|-------------------|---------|
| L0 | OS/Hardware | C++, Rust, C | Low-level system operations |
| L1 | Core Engine | TypeScript, Python | Core business logic |
| L2 | Governance | Python, Rego | Policy enforcement |
| L3 | AI/Automation | Python, TypeScript | Intelligent automation |
| L4 | Services | Go, TypeScript | Microservices |
| L5 | Applications | TypeScript, React | User interfaces |

---

## 🚀 Usage

### Accessing the Dashboard

1. **Development:**

   ```bash
   cd apps/web
   npm run dev
   ```

   Navigate to: `http://localhost:3000/#/language-governance`

2. **Production:**
   Build and deploy the web app, then access via your domain

### Running the API Standalone

```bash
cd apps/web/services/api
python language_governance.py
```

API available at: `http://localhost:8000`

### Running CI Workflow Manually

```bash
# Via GitHub UI
Actions → Language Governance Dashboard Update → Run workflow

# Via GitHub CLI
gh workflow run language-governance-dashboard.yml
```

---

## 📝 Governance Data Format

### Language Governance Report (Markdown)

```markdown
# Language Governance Report v1.0

## Executive Summary
| Metric | Value | Status |
|--------|-------|--------|
| Health Score | 85/100 | ✅ Good |
...

## Violations List
- **file.ts** — Violation description (Layer: L5)
...
```

### Semgrep Report (JSON)

```json
{
  "errors": [],
  "results": [
    {
      "check_id": "rule.id",
      "path": "file/path",
      "extra": {
        "message": "Issue description",
        "severity": "WARNING"
      }
    }
  ]
}
```

### Language History (YAML)

```yaml
events:
  - timestamp: '2025-12-06T14:30:00Z'
    event: 'Auto-fix applied'
    details: 'Fixed violations'
    type: 'fix'
    author: 'auto-fix-bot'
```

---

## 🔧 Configuration

### Environment Variables

- `VITE_API_URL` - API base URL (default: `http://localhost:8000`)

### API Configuration

Edit `apps/web/services/api.py` to customize:

- Data sources
- Health score calculation
- Report parsing logic

### Dashboard Customization

Edit `apps/web/src/pages/LanguageGovernance.tsx` to customize:

- Metrics displayed
- Visualization style
- Color schemes
- Layout

---

## 🧪 Testing

### Manual Testing

1. Start the API:

   ```bash
   cd apps/web
   python services/api.py
   ```

2. Start the frontend:

   ```bash
   cd apps/web
   npm run dev
   ```

3. Visit: `http://localhost:3000/#/language-governance`

### Verify Data Loading

Check browser console for:

- API requests
- Data fetching
- Error messages

### Test CI Workflow

```bash
# Create test branch
git checkout -b test-dashboard

# Trigger workflow by push
git commit --allow-empty -m "test: trigger dashboard update"
git push origin test-dashboard
```

---

## 📈 Health Score Calculation

```
Health Score = 100 - (Security Findings × 5)

Grade Scale:
- A: 90-100 (Excellent)
- B: 80-89 (Good)
- C: 70-79 (Fair)
- D: 60-69 (Poor)
- F: 0-59 (Critical)
```

---

## 🎯 Future Enhancements

Potential improvements mentioned in the requirements:

1. **Sankey Diagram** - Language flow visualization
2. **Hotspot Heatmap** - Violation concentration map
3. **Interactive Knowledge Graph** - Neo4j/D3.js integration
4. **Auto-remediation Chain** - Governance → Refactor → Fix → Visualize
5. **Trend Analysis** - Historical health score charts
6. **Real-time Updates** - WebSocket integration
7. **Multi-repository Support** - Dashboard for multiple projects

---

## 📚 Resources

- [Mermaid Documentation](https://mermaid.js.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Semgrep Rules](https://semgrep.dev/docs/rules/)

---

## 🤝 Contributing

To contribute to the Language Governance Dashboard:

1. Make changes to relevant files
2. Test locally using the manual testing steps
3. Run the build: `npm run build`
4. Commit with descriptive messages
5. Submit PR for review

---

## 📄 License

MIT License - See project root LICENSE file

---

**Maintained by:** SynergyMesh Team  
**Last Updated:** 2025-12-06  
**Version:** 1.0.0
