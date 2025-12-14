# 🤖 AI 模型部署指南 | AI Model Deployment Guide

**文档版本**: 1.0.0  
**最后更新**: 2025-12-14  
**适用系统**: Unmanned Island System / SynergyMesh Platform

---

## 📋 目录 | Table of Contents

1. [概述](#概述)
2. [硬件要求](#硬件要求)
3. [推荐配置](#推荐配置)
4. [vLLM 部署](#vllm-部署)
5. [模型配置](#模型配置)
6. [性能优化](#性能优化)
7. [故障排查](#故障排查)

---

## 🎯 概述

本指南详细说明 AI 模型（特别是大语言模型 LLM）在 Unmanned Island System 中的部署要求和最佳实践。

### 支持的模型类型

- **大语言模型 (LLM)**: GPT, LLaMA, Qwen 等
- **嵌入模型 (Embedding)**: 向量化和语义搜索
- **代码生成模型**: CodeLLaMA, StarCoder 等
- **多模态模型**: Vision-Language 模型

---

## 💻 硬件要求

### ⚠️ 最低运行配置

**GPU 要求**:

- **显存**: 24GB
- **推荐卡型**: NVIDIA RTX 4090, RTX 3090
- **限制**: 仅能拉起模型，无法达到完整长度

**配置说明**:

```yaml
# 最低配置限制
max_model_len: 14000  # 最大上下文长度：12500-14000
gpu_memory_utilization: 0.90  # GPU 显存使用率
tensor_parallel_size: 1  # 单卡部署
```

**性能特点**:

- ✅ 可以启动和运行模型
- ⚠️ 上下文长度受限（需要设置 max_len）
- ⚠️ 可能出现 OOM（内存不足）
- ⚠️ 不推荐用于生产环境

### ✅ 推荐运行配置

**GPU 要求**:

- **显存**: 30GB 或以上
- **推荐卡型**:
  - NVIDIA A100 (40GB/80GB)
  - NVIDIA H100 (80GB)
  - NVIDIA H800
- **优势**: 能完整部署模型以及完整长度上下文

**配置说明**:

```yaml
# 推荐配置
max_model_len: 32768  # 完整上下文长度
gpu_memory_utilization: 0.95  # 高 GPU 显存使用率
tensor_parallel_size: 1  # 单卡或多卡
enable_prefix_caching: true  # 启用前缀缓存
```

**性能特点**:

- ✅ 完整上下文长度支持
- ✅ 稳定的推理性能
- ✅ 适合生产环境
- ✅ 支持批处理和并发请求

### 📊 配置对比表

| 配置项 | 最低配置 (24GB) | 推荐配置 (30GB+) |
|--------|----------------|------------------|
| GPU 型号 | RTX 4090 | A100/H100 |
| 显存 | 24GB | 30GB-80GB |
| 上下文长度 | 12500-14000 | 32768+ |
| 批处理大小 | 1-4 | 8-32 |
| 并发请求 | 受限 | 高 |
| 生产就绪 | ❌ | ✅ |

---

## 🚀 推荐配置

### 操作系统选择

**强烈推荐**:

- **Ubuntu 22.04 LTS** ✅
- **Ubuntu 20.04 LTS** ✅
- **其他 Linux 开源版本** (Debian, CentOS Stream, Rocky Linux) ✅

**原因**:

1. 完整支持 vLLM
2. CUDA 驱动兼容性好
3. 容器化部署稳定
4. 社区支持完善

**不推荐**:

- ❌ Windows (WSL2 可用但性能受限)
- ❌ macOS (无 NVIDIA GPU 支持)

### CUDA 和驱动要求

```bash
# 检查 NVIDIA 驱动
nvidia-smi

# 要求版本
CUDA: >= 11.8
Driver: >= 520.00
```

---

## 🐳 vLLM 部署

### 方法 1: Docker 部署（推荐）

#### 步骤 1: 拉取官方镜像

```bash
# 拉取 vLLM OpenAI 兼容服务器镜像
docker pull vllm/vllm-openai:v0.12.0
```

#### 步骤 2: 启动容器

```bash
# 基础启动（最低配置）
docker run --gpus all \
  --name vllm-server \
  -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:v0.12.0 \
  --model Qwen/Qwen2.5-7B-Instruct \
  --max-model-len 14000 \
  --gpu-memory-utilization 0.90

# 推荐配置启动
docker run --gpus all \
  --name vllm-server \
  -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:v0.12.0 \
  --model Qwen/Qwen2.5-7B-Instruct \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.95 \
  --enable-prefix-caching \
  --trust-remote-code
```

#### 步骤 3: 进入容器并更新依赖

```bash
# 进入容器
docker exec -it vllm-server bash

# 更新 transformers 到最新预览版
pip install -U transformers --pre

# 验证安装
python -c "import transformers; print(transformers.__version__)"
```

#### 步骤 4: 验证服务

```bash
# 健康检查
curl http://localhost:8000/health

# 测试推理
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "prompt": "Hello, how are you?",
    "max_tokens": 100
  }'
```

### 方法 2: Docker Compose 部署

创建 `docker-compose.vllm.yml`:

```yaml
version: '3.8'

services:
  vllm-server:
    image: vllm/vllm-openai:v0.12.0
    container_name: vllm-server
    ports:
      - "8000:8000"
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
      - ./models:/models
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - HF_HOME=/root/.cache/huggingface
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    command: >
      --model Qwen/Qwen2.5-7B-Instruct
      --max-model-len 32768
      --gpu-memory-utilization 0.95
      --enable-prefix-caching
      --trust-remote-code
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

启动:

```bash
# 启动服务
docker-compose -f docker-compose.vllm.yml up -d

# 查看日志
docker-compose -f docker-compose.vllm.yml logs -f

# 停止服务
docker-compose -f docker-compose.vllm.yml down
```

### 方法 3: 原生安装

```bash
# 创建虚拟环境
python3 -m venv vllm-env
source vllm-env/bin/activate

# 安装 vLLM
pip install vllm

# 更新 transformers
pip install -U transformers --pre

# 启动服务器
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-7B-Instruct \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.95
```

---

## ⚙️ 模型配置

### 配置参数详解

#### 核心参数

| 参数 | 24GB 配置 | 30GB+ 配置 | 说明 |
|------|-----------|------------|------|
| `--max-model-len` | 12500-14000 | 32768 | 最大上下文长度 |
| `--gpu-memory-utilization` | 0.90 | 0.95 | GPU 显存使用率 |
| `--tensor-parallel-size` | 1 | 1-2 | 张量并行度（多卡） |
| `--enable-prefix-caching` | false | true | 前缀缓存 |

#### 性能调优参数

```bash
# 批处理优化
--max-num-batched-tokens 8192  # 批处理 token 数
--max-num-seqs 256  # 最大并发序列数

# 量化加速（降低显存占用）
--quantization awq  # AWQ 量化
--quantization gptq  # GPTQ 量化

# KV 缓存优化
--block-size 16  # KV 缓存块大小
--swap-space 4  # CPU 交换空间 (GB)
```

### 环境变量配置

```bash
# Hugging Face 缓存路径
export HF_HOME=/path/to/cache
export TRANSFORMERS_CACHE=/path/to/cache

# CUDA 可见设备
export CUDA_VISIBLE_DEVICES=0,1  # 使用 GPU 0 和 1

# vLLM 配置
export VLLM_LOGGING_LEVEL=INFO
export VLLM_USE_MODELSCOPE=false
```

### 多模型配置

```yaml
# config/ai-models.yaml
models:
  - name: code-generation
    model_path: "codellama/CodeLlama-7b-Instruct-hf"
    max_len: 16384
    gpu_memory: 0.45
    
  - name: chat-model
    model_path: "Qwen/Qwen2.5-7B-Instruct"
    max_len: 32768
    gpu_memory: 0.45
```

---

## 🔧 性能优化

### 显存优化策略

#### 1. 模型量化

```bash
# AWQ 量化（推荐）
--quantization awq
--model TheBloke/Llama-2-7B-AWQ

# GPTQ 量化
--quantization gptq
--model TheBloke/Llama-2-7B-GPTQ
```

#### 2. 动态批处理

```bash
# 启用动态批处理
--max-num-batched-tokens 4096
--max-num-seqs 128
```

#### 3. 前缀缓存

```bash
# 启用前缀缓存（推荐配置）
--enable-prefix-caching
```

### 吞吐量优化

```bash
# 多 GPU 张量并行
--tensor-parallel-size 2  # 2 卡并行

# Pipeline 并行（超大模型）
--pipeline-parallel-size 2

# 增加工作线程
--worker-use-ray
```

### 延迟优化

```bash
# 减少批处理延迟
--max-num-batched-tokens 2048
--max-num-seqs 64

# 使用流式输出
--stream-output
```

---

## 🐛 故障排查

### 常见问题

#### 1. OOM (Out of Memory) 错误

**症状**:

```text
RuntimeError: CUDA out of memory
```

**解决方案**:

```bash
# 方案 1: 降低 max-model-len
--max-model-len 12000

# 方案 2: 降低 GPU 显存使用率
--gpu-memory-utilization 0.85

# 方案 3: 减少批处理大小
--max-num-batched-tokens 2048

# 方案 4: 使用量化模型
--quantization awq
```

#### 2. CUDA 不可用

**症状**:

```text
RuntimeError: No CUDA GPUs are available
```

**检查步骤**:

```bash
# 1. 检查 NVIDIA 驱动
nvidia-smi

# 2. 检查 CUDA 版本
nvcc --version

# 3. 验证 PyTorch CUDA
python -c "import torch; print(torch.cuda.is_available())"

# 4. 重新安装 vLLM（匹配 CUDA 版本）
pip uninstall vllm
pip install vllm-cuda118  # CUDA 11.8
# 或
pip install vllm-cuda121  # CUDA 12.1
```

#### 3. 模型加载失败

**症状**:

```text
OSError: Can't load tokenizer for 'model_name'
```

**解决方案**:

```bash
# 1. 更新 transformers
pip install -U transformers --pre

# 2. 清除缓存
rm -rf ~/.cache/huggingface/*

# 3. 手动下载模型
huggingface-cli download Qwen/Qwen2.5-7B-Instruct

# 4. 使用本地路径
--model /path/to/local/model
```

#### 4. 性能不佳

**诊断工具**:

```bash
# 监控 GPU 使用
watch -n 1 nvidia-smi

# 查看 vLLM 统计
curl http://localhost:8000/metrics

# 压力测试
python benchmark.py \
  --model Qwen/Qwen2.5-7B-Instruct \
  --num-prompts 100 \
  --max-tokens 512
```

**优化建议**:

1. 启用前缀缓存: `--enable-prefix-caching`
2. 调整批处理大小
3. 使用量化模型
4. 考虑多 GPU 部署

#### 5. Docker 容器无法访问 GPU

**症状**:

```text
docker: Error response from daemon: could not select device driver
```

**解决方案**:

```bash
# 1. 安装 NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 2. 重启 Docker
sudo systemctl restart docker

# 3. 测试 GPU 访问
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### 日志和监控

#### 启用详细日志

```bash
# vLLM 日志级别
export VLLM_LOGGING_LEVEL=DEBUG

# Python 日志
export PYTHONPATH=/app
python -m vllm.entrypoints.openai.api_server --log-level debug
```

#### 监控端点

```bash
# 健康检查
curl http://localhost:8000/health

# Prometheus 指标
curl http://localhost:8000/metrics

# 模型信息
curl http://localhost:8000/v1/models
```

---

## 📚 集成到 SynergyMesh

### 配置文件集成

在 `config/ai-constitution.yaml` 中添加:

```yaml
ai_models:
  llm:
    provider: vllm
    endpoint: http://localhost:8000
    model: Qwen/Qwen2.5-7B-Instruct
    max_tokens: 32768
    temperature: 0.7
    
  embedding:
    provider: sentence-transformers
    model: BAAI/bge-large-zh-v1.5
```

### 服务发现

在 `core/unified_integration/` 中注册 AI 服务:

```python
# core/unified_integration/ai_service_registry.py
from core.services.ai_client import VLLMClient

def register_ai_services():
    """注册 AI 模型服务"""
    vllm_client = VLLMClient(
        base_url="http://localhost:8000",
        model="Qwen/Qwen2.5-7B-Instruct"
    )
    
    registry.register("ai.llm", vllm_client)
```

### 健康检查集成

在 `scripts/health-check.sh` 中添加:

```bash
# 检查 vLLM 服务
check_vllm_health() {
  local url="http://localhost:8000/health"
  if curl -sf "$url" > /dev/null; then
    echo "✅ vLLM service is healthy"
    return 0
  else
    echo "❌ vLLM service is unhealthy"
    return 1
  fi
}
```

---

## 🔗 参考资源

### 官方文档

- [vLLM 官方文档](https://docs.vllm.ai/)
- [vLLM GitHub](https://github.com/vllm-project/vllm)
- [Transformers 文档](https://huggingface.co/docs/transformers/)

### 相关文档

- [AI Module README](../ai/README.md)
- [部署指南](./DEPLOYMENT_GUIDE.md)
- [系统架构](./SYSTEM_ARCHITECTURE.md)

### 社区支持

- GitHub Issues: [vLLM Issues](https://github.com/vllm-project/vllm/issues)
- Discord: vLLM Community
- Hugging Face Forums

---

## 📝 更新日志

### v1.0.0 (2025-12-14)

- ✅ 初始版本
- ✅ 添加硬件要求说明（24GB 最低 / 30GB 推荐）
- ✅ vLLM Docker 部署指南
- ✅ 配置参数详解
- ✅ 故障排查指南
- ✅ SynergyMesh 集成说明

---

## 🤝 贡献

如有问题或建议，请提交 Issue 或 Pull Request。

**维护者**: SynergyMesh Team  
**联系方式**: [GitHub Issues](https://github.com/SynergyMesh-master/KeyStonOps/issues)
