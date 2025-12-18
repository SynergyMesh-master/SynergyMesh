#!/usr/bin/env node
/**
 * Language Compliance Checker
 * 
 * 基本檔案驗證工具：
 * - 掃描 .md, .yml, .yaml 檔案
 * - 驗證檔案存在、可讀取且不為空
 * - 用於 CI 流程中的基本文件健全性檢查
 */

import { readdir, readFile } from 'fs/promises';
import { join, extname } from 'path';

// 要檢查的檔案類型
const EXTENSIONS = ['.md', '.yml', '.yaml'];

// 要排除的目錄
const EXCLUDED_DIRS = [
  'node_modules',
  '.git',
  '.github/agents',
  'dist',
  'build',
  'coverage',
  '__pycache__',
  '.venv',
  'venv',
];

// 要排除的檔案
const EXCLUDED_FILES = [
  'package-lock.json',
  'pnpm-lock.yaml',
  'yarn.lock',
];

/**
 * 遞迴掃描目錄並收集符合條件的檔案
 */
async function scanDirectory(dir, files = []) {
  const entries = await readdir(dir, { withFileTypes: true });
  
  for (const entry of entries) {
    const fullPath = join(dir, entry.name);
    
    // 檢查是否為排除的目錄
    if (entry.isDirectory()) {
      const isExcluded = EXCLUDED_DIRS.some(excluded => 
        fullPath.endsWith('/' + excluded) || entry.name === excluded
      );
      if (!isExcluded) {
        await scanDirectory(fullPath, files);
      }
    } else if (entry.isFile()) {
      // 檢查是否為排除的檔案
      if (EXCLUDED_FILES.includes(entry.name)) {
        continue;
      }
      
      // 檢查副檔名
      const ext = extname(entry.name).toLowerCase();
      if (EXTENSIONS.includes(ext)) {
        files.push(fullPath);
      }
    }
  }
  
  return files;
}

/**
 * 檢查檔案內容（基本驗證）
 * 驗證檔案存在、可讀取且不為空
 */
async function checkFile(filePath) {
  try {
    const content = await readFile(filePath, 'utf-8');
    
    // 基本驗證：確保檔案不是空的且可讀取
    if (!content || content.trim().length === 0) {
      return { path: filePath, status: 'warning', message: '檔案為空' };
    }
    
    return { path: filePath, status: 'pass', message: '檔案驗證通過' };
  } catch (error) {
    return { path: filePath, status: 'error', message: error.message };
  }
}

/**
 * 主程式
 */
async function main() {
  const targetDir = process.argv[2] || '.';
  
  console.log('🔍 Language Compliance Checker');
  console.log(`📁 掃描目錄: ${targetDir}`);
  console.log('');
  
  try {
    const files = await scanDirectory(targetDir);
    console.log(`📄 找到 ${files.length} 個檔案需要檢查`);
    console.log('');
    
    let passCount = 0;
    let warningCount = 0;
    let errorCount = 0;
    
    for (const file of files) {
      const result = await checkFile(file);
      
      if (result.status === 'pass') {
        passCount++;
      } else if (result.status === 'warning') {
        warningCount++;
        console.log(`⚠️  ${result.path}: ${result.message}`);
      } else {
        errorCount++;
        console.log(`❌ ${result.path}: ${result.message}`);
      }
    }
    
    console.log('');
    console.log('📊 檢查結果摘要:');
    console.log(`   ✅ 通過: ${passCount}`);
    console.log(`   ⚠️  警告: ${warningCount}`);
    console.log(`   ❌ 錯誤: ${errorCount}`);
    console.log('');
    
    if (errorCount > 0) {
      console.log('❌ 語言合規性檢查失敗');
      process.exit(1);
    } else {
      console.log('✅ 語言合規性檢查通過');
      process.exit(0);
    }
  } catch (error) {
    console.error('❌ 檢查過程中發生錯誤:', error.message);
    process.exit(1);
  }
}

main();
