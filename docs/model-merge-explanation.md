# 模型合并说明文档

## 问题描述

当你使用 Qwen3.5-0.8B（多模态模型）进行训练并合并模型时，会发现：
- **基础模型大小**: 1.7GB (Qwen3.5-0.8B)
- **合并后模型大小**: 1.4GB (变小了)

这是**正常现象**，不是 bug。

## 原因分析

### 1. Qwen3.5 模型架构

Qwen3.5-0.8B 是一个**多模态模型**，包含两个主要部分：

```
Qwen3.5ForConditionalGeneration
├── 文本编码器 (Text Encoder)     ~1.4GB
│   ├── 24 层 Transformer 层
│   ├── 词嵌入层
│   └── 语言模型头
│
└── 视觉编码器 (Vision Encoder)   ~300MB
    ├── 12 层 ViT 层
    ├── 图像 patch 嵌入
    └── 视觉特征投影
```

### 2. LoRA 训练过程

在训练过程中：
- ✅ **文本部分**：参与训练，学习你的数据集（酒店客服对话）
- ❌ **视觉部分**：**冻结**，不参与训练，保持预训练权重

这是因为：
1. 训练数据是纯文本（JSONL 格式的对话）
2. 训练脚本使用 `AutoModelForCausalLM` 只加载文本部分
3. LoRA adapter 只适配文本层的参数

### 3. 合并过程

合并时使用的 `AutoModelForCausalLM.from_pretrained()` 会：
- 只加载**文本部分**的权重
- 忽略视觉编码器
- 将 LoRA 权重合并到文本部分

因此，合并后的模型：
- ✅ 包含完整的文本能力（1.4GB）
- ❌ 不包含视觉编码器（节省了 ~300MB）

## 这对你的应用有什么影响？

### 场景 1：纯文本应用（推荐）✅

如果你的应用场景是**酒店客服对话**（纯文本）：
- ✅ **合并后的模型完全够用**
- ✅ 不需要视觉能力
- ✅ 模型更小，推理更快
- ✅ 部署更简单

**建议**：使用合并后的模型即可

### 场景 2：需要视觉能力

如果你需要处理**图片 + 文本**的多模态任务：
- ❌ 合并后的模型**无法使用**
- ⚠️ 需要使用以下方式之一：

#### 方案 A：使用基础模型 + LoRA adapter
```python
from transformers import AutoModelForConditionalGeneration
from peft import PeftModel

# 加载完整的多模态基础模型
base_model = AutoModelForConditionalGeneration.from_pretrained(
    'models/Qwen3.5-0.8B',
    trust_remote_code=True
)

# 加载 LoRA adapter
model = PeftModel.from_pretrained(base_model, 'models/hotel_task1')

# 现在可以处理图像 + 文本输入
```

#### 方案 B：手动合并（复杂，不推荐）
需要修改 `merge_lora.py` 使用 `AutoModel` 而不是 `AutoModelForCausalLM`，
但由于依赖问题（需要 `flash-linear-attention` 和 `causal-conv1d`），
在 CPU 环境下会失败。

## 技术细节

### 为什么依赖安装失败？

Qwen3.5 使用了特殊的注意力机制：
- **Gated DeltaNet**（线性注意力）
- **Mamba SSM**（状态空间模型）

这些需要：
1. `flash-linear-attention` - Flash 注意力实现
2. `causal-conv1d` - 因果卷积（需要 CUDA 支持）

在 Windows + CPU PyTorch 环境下，这些库无法编译安装。

### 模型架构对比

**原始模型 config.json**:
```json
{
  "architectures": ["Qwen3_5ForConditionalGeneration"],
  "model_type": "qwen3_5",
  "vision_config": {...},  // 视觉配置
  "image_token_id": 248056,
  "text_config": {...}
}
```

**合并后模型 config.json**:
```json
{
  "architectures": ["Qwen3_5ForCausalLM"],
  "model_type": "qwen3_5_text",
  // 没有 vision_config
  // 没有 image_token_id
  // 只有文本配置
}
```

## 总结

| 项目 | 基础模型 | 合并后模型 |
|------|---------|-----------|
| 大小 | 1.7GB | 1.4GB |
| 架构 | Qwen3_5ForConditionalGeneration | Qwen3_5ForCausalLM |
| 视觉编码器 | ✅ 有 | ❌ 无 |
| 文本能力 | ✅ 完整 | ✅ 完整（已微调） |
| 适用场景 | 多模态任务 | 纯文本任务 |

**对于酒店客服场景，合并后的 1.4GB 模型是最佳选择！**

## 相关文件

- 合并脚本：`scripts/merge_lora.py`
- 训练脚本：`scripts/train_model.py`
- 需求文件：`requirements-train.txt`

## 参考链接

- [Qwen3.5 官方文档](https://huggingface.co/Qwen/Qwen3.5-0.8B)
- [PEFT 库文档](https://huggingface.co/docs/peft)
- [LoRA 合并最佳实践](https://github.com/huggingface/peft/issues/1168)
