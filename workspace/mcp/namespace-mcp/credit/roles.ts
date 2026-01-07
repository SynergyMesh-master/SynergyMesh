/**
 * CRediT Contributor Roles - Clinical Dissection Edition
 * @module dissect::credit
 * @description ANSI/NISO Z39.104-2022 with honest naming
 * @version 2.0.0
 * @standard ANSI/NISO Z39.104-2022
 * @style 臨床反諷 | 誠實命名 | 不包裝
 */

// ============================================================================
// CREDIT ROLE DEFINITIONS (ANSI/NISO Z39.104-2022)
// ============================================================================

/**
 * The 14 CRediT contributor roles - with honest descriptions
 */
export const CREDIT_ROLES = {
  CONCEPTUALIZATION: 'conceptualization',
  DATA_CURATION: 'data_curation',
  FORMAL_ANALYSIS: 'formal_analysis',
  FUNDING_ACQUISITION: 'funding_acquisition',
  INVESTIGATION: 'investigation',
  METHODOLOGY: 'methodology',
  PROJECT_ADMINISTRATION: 'project_administration',
  RESOURCES: 'resources',
  SOFTWARE: 'software',
  SUPERVISION: 'supervision',
  VALIDATION: 'validation',
  VISUALIZATION: 'visualization',
  WRITING_ORIGINAL_DRAFT: 'writing_original_draft',
  WRITING_REVIEW_EDITING: 'writing_review_editing'
} as const;

export type CreditRoleId = typeof CREDIT_ROLES[keyof typeof CREDIT_ROLES];

// ============================================================================
// CLINICAL ROLE MAPPING - 臨床反諷版本
// ============================================================================

/**
 * Clinical namespace identifiers - honest about what we do
 */
export const CLINICAL_ROLES = {
  // A類: 包裝真相的人
  IDEA_PACKAGING: 'facade.idea_packaging',
  METHOD_THEATRE: 'dissect.method_theatre',
  MONEY_HUNTING: 'reality.money_hunting',
  HERDING_CATS: 'ops.herding_cats',

  // B類: 實際幹活的人
  DIG_DIRT: 'archaeology.dig_dirt',
  DATA_JANITOR: 'dissect.data_janitor',
  NUMBER_TORTURE: 'audit.number_torture',
  CODE_MONKEY: 'ops.code_monkey',
  STUFF_PROVIDER: 'ops.stuff_provider',
  MAKE_PRETTY: 'facade.make_pretty',
  FIRST_DRAFT_LIES: 'artifact.first_draft_lies',
  POLISH_THE_LIES: 'artifact.polish_the_lies',

  // C類: 找碴的人
  REALITY_CHECK: 'audit.reality_check',
  ADULT_SUPERVISION: 'audit.adult_supervision'
} as const;

export type ClinicalRoleId = typeof CLINICAL_ROLES[keyof typeof CLINICAL_ROLES];

/**
 * Complete role definition with clinical mapping
 */
export interface CreditRoleDefinition {
  readonly id: CreditRoleId;
  readonly name: string;
  readonly nameCN: string;
  readonly description: string;
  readonly descriptionCN: string;
  /** 臨床反諷解讀 */
  readonly honestDescription: string;
  readonly category: CreditRoleCategory;
  /** 臨床映射 */
  readonly clinicalRole: ClinicalRoleId;
  readonly dependsOn: CreditRoleId[];
  readonly workflowOrder: number;
}

export type CreditRoleCategory =
  | 'structural'    // A類: 包裝真相的人
  | 'operational'   // B類: 實際幹活的人
  | 'validation';   // C類: 找碴的人

// ============================================================================
// CREDIT → CLINICAL MAPPING (反諷版)
// ============================================================================

export const CREDIT_TO_CLINICAL_MAP: Record<CreditRoleId, ClinicalRoleId> = {
  conceptualization: 'facade.idea_packaging',
  methodology: 'dissect.method_theatre',
  funding_acquisition: 'reality.money_hunting',
  project_administration: 'ops.herding_cats',
  investigation: 'archaeology.dig_dirt',
  data_curation: 'dissect.data_janitor',
  formal_analysis: 'audit.number_torture',
  software: 'ops.code_monkey',
  resources: 'ops.stuff_provider',
  visualization: 'facade.make_pretty',
  writing_original_draft: 'artifact.first_draft_lies',
  writing_review_editing: 'artifact.polish_the_lies',
  validation: 'audit.reality_check',
  supervision: 'audit.adult_supervision'
};

// ============================================================================
// COMPLETE ROLE DEFINITIONS (臨床版)
// ============================================================================

export const CREDIT_ROLE_DEFINITIONS: readonly CreditRoleDefinition[] = [
  {
    id: 'conceptualization',
    name: 'Conceptualization',
    nameCN: '概念化',
    description: 'Ideas; formulation or evolution of overarching research goals and aims.',
    descriptionCN: '構思；制定或發展整體研究目標和目的。',
    honestDescription: '把想法包裝成看起來很厲害的樣子',
    category: 'structural',
    clinicalRole: 'facade.idea_packaging',
    dependsOn: [],
    workflowOrder: 1
  },
  {
    id: 'methodology',
    name: 'Methodology',
    nameCN: '方法論',
    description: 'Development or design of methodology; creation of models.',
    descriptionCN: '方法論的發展或設計；模型的創建。',
    honestDescription: '方法論表演 - 讓過程看起來很科學',
    category: 'structural',
    clinicalRole: 'dissect.method_theatre',
    dependsOn: ['conceptualization'],
    workflowOrder: 2
  },
  {
    id: 'funding_acquisition',
    name: 'Funding Acquisition',
    nameCN: '資金籌集',
    description: 'Acquisition of the financial support for the project.',
    descriptionCN: '為計畫籌集資金。',
    honestDescription: '找錢的人 - 這才是真正重要的技能',
    category: 'structural',
    clinicalRole: 'reality.money_hunting',
    dependsOn: ['conceptualization'],
    workflowOrder: 3
  },
  {
    id: 'project_administration',
    name: 'Project Administration',
    nameCN: '專案管理',
    description: 'Management and coordination responsibility for research activity.',
    descriptionCN: '負責研究活動規劃和執行的管理和協調。',
    honestDescription: '趕貓 - 試圖讓一群不想合作的人合作',
    category: 'structural',
    clinicalRole: 'ops.herding_cats',
    dependsOn: ['conceptualization', 'methodology'],
    workflowOrder: 4
  },
  {
    id: 'resources',
    name: 'Resources',
    nameCN: '資源',
    description: 'Provision of study materials, instrumentation, computing resources.',
    descriptionCN: '提供學習材料、儀器、計算資源或其他分析工具。',
    honestDescription: '提供東西的人 - 有錢能使鬼推磨',
    category: 'operational',
    clinicalRole: 'ops.stuff_provider',
    dependsOn: ['funding_acquisition'],
    workflowOrder: 5
  },
  {
    id: 'investigation',
    name: 'Investigation',
    nameCN: '調查',
    description: 'Conducting research process, performing experiments or data collection.',
    descriptionCN: '進行研究和調查過程，進行實驗或數據收集。',
    honestDescription: '挖泥巴 - 實際動手挖掘數據的人',
    category: 'operational',
    clinicalRole: 'archaeology.dig_dirt',
    dependsOn: ['methodology', 'resources'],
    workflowOrder: 6
  },
  {
    id: 'data_curation',
    name: 'Data Curation',
    nameCN: '資料整理',
    description: 'Annotate, scrub data and maintain research data.',
    descriptionCN: '註釋、清理資料以及維護研究資料。',
    honestDescription: '數據清潔工 - 把髒數據擦乾淨',
    category: 'operational',
    clinicalRole: 'dissect.data_janitor',
    dependsOn: ['investigation'],
    workflowOrder: 7
  },
  {
    id: 'formal_analysis',
    name: 'Formal Analysis',
    nameCN: '形式分析',
    description: 'Application of statistical, mathematical techniques to analyse data.',
    descriptionCN: '運用統計學、數學技術來分析資料。',
    honestDescription: '折磨數字直到它招供 - 總能找到想要的結論',
    category: 'operational',
    clinicalRole: 'audit.number_torture',
    dependsOn: ['data_curation'],
    workflowOrder: 8
  },
  {
    id: 'software',
    name: 'Software',
    nameCN: '軟體',
    description: 'Programming, software development; implementation of code.',
    descriptionCN: '程式設計、軟體開發；實作程式碼和演算法。',
    honestDescription: '碼農 - 把鍵盤敲爛的人',
    category: 'operational',
    clinicalRole: 'ops.code_monkey',
    dependsOn: ['methodology'],
    workflowOrder: 9
  },
  {
    id: 'visualization',
    name: 'Visualization',
    nameCN: '視覺化',
    description: 'Preparation of visualization/data presentation.',
    descriptionCN: '視覺化/資料展示的準備和創作。',
    honestDescription: '讓它變漂亮 - 用圖表掩蓋數據的醜陋',
    category: 'operational',
    clinicalRole: 'facade.make_pretty',
    dependsOn: ['formal_analysis'],
    workflowOrder: 10
  },
  {
    id: 'validation',
    name: 'Validation',
    nameCN: '驗證',
    description: 'Verification of replication/reproducibility of results.',
    descriptionCN: '驗證結果的可重複性/可再現性。',
    honestDescription: '現實檢查 - 看看是不是在自欺欺人',
    category: 'validation',
    clinicalRole: 'audit.reality_check',
    dependsOn: ['formal_analysis', 'software'],
    workflowOrder: 11
  },
  {
    id: 'writing_original_draft',
    name: 'Writing – Original Draft',
    nameCN: '寫作 - 初稿',
    description: 'Writing the initial draft.',
    descriptionCN: '撰寫初稿。',
    honestDescription: '初稿謊言 - 第一版總是充滿誇大和省略',
    category: 'operational',
    clinicalRole: 'artifact.first_draft_lies',
    dependsOn: ['formal_analysis', 'visualization'],
    workflowOrder: 12
  },
  {
    id: 'writing_review_editing',
    name: 'Writing – Review & Editing',
    nameCN: '寫作 - 審閱與編輯',
    description: 'Critical review, commentary or revision.',
    descriptionCN: '批判性審查、評論或修訂。',
    honestDescription: '潤色謊言 - 讓謊言更難被發現',
    category: 'operational',
    clinicalRole: 'artifact.polish_the_lies',
    dependsOn: ['writing_original_draft'],
    workflowOrder: 13
  },
  {
    id: 'supervision',
    name: 'Supervision',
    nameCN: '監督',
    description: 'Oversight and leadership responsibility, including mentorship.',
    descriptionCN: '監督和領導工作，包括對團隊外部人員的指導。',
    honestDescription: '大人監督 - 確保小朋友不會搞砸',
    category: 'validation',
    clinicalRole: 'audit.adult_supervision',
    dependsOn: ['validation'],
    workflowOrder: 14
  }
] as const;

// ============================================================================
// ROLE LOOKUP UTILITIES
// ============================================================================

export function getRoleDefinition(roleId: CreditRoleId): CreditRoleDefinition | undefined {
  return CREDIT_ROLE_DEFINITIONS.find(r => r.id === roleId);
}

export function getRolesByCategory(category: CreditRoleCategory): CreditRoleDefinition[] {
  return CREDIT_ROLE_DEFINITIONS.filter(r => r.category === category);
}

export function getClinicalRole(creditRole: CreditRoleId): ClinicalRoleId {
  return CREDIT_TO_CLINICAL_MAP[creditRole];
}

export function getRolesInWorkflowOrder(): CreditRoleDefinition[] {
  return [...CREDIT_ROLE_DEFINITIONS].sort((a, b) => a.workflowOrder - b.workflowOrder);
}

// ============================================================================
// MACHINE-NATIVE JSON EXPORTS (Minified)
// ============================================================================

/**
 * Single-line JSON for .governance files - clinical edition
 */
export const CREDIT_TO_CLINICAL_JSON = JSON.stringify({
  credit_to_clinical: CREDIT_TO_CLINICAL_MAP
});

/**
 * Minified with honest descriptions
 */
export const CREDIT_ROLES_MINIFIED = JSON.stringify(
  CREDIT_ROLE_DEFINITIONS.map(r => ({
    id: r.id,
    cat: r.category[0], // s=structural, o=operational, v=validation
    cli: r.clinicalRole,
    ord: r.workflowOrder,
    dep: r.dependsOn,
    honest: r.honestDescription
  }))
);

// ============================================================================
// CATEGORY DESCRIPTIONS (臨床版)
// ============================================================================

export const CATEGORY_DESCRIPTIONS = {
  structural: {
    name: 'Structural',
    nameCN: '結構層',
    clinicalName: '包裝真相的人',
    description: 'Those who package truth to look impressive'
  },
  operational: {
    name: 'Operational',
    nameCN: '執行層',
    clinicalName: '實際幹活的人',
    description: 'Those who actually do the work'
  },
  validation: {
    name: 'Validation',
    nameCN: '驗證層',
    clinicalName: '找碴的人',
    description: 'Those who find problems (thankless job)'
  }
} as const;
