# GPU 使用指南

## 自动检测和安装

### 1. 检测 GPU 状态
在任务管理页面点击"检测 GPU"按钮，系统会显示：
- NVIDIA GPU 信息
- CUDA 版本
- PyTorch CUDA 支持情况
- 推荐安装方案

### 2. 自动安装 GPU 版本
如果检测到 GPU，可以点击"安装 GPU 版本 PyTorch"按钮进行自动安装。

也可以手动执行：
```bash
python scripts/install_torch.py
```

## 手动安装

### 有 NVIDIA GPU 的情况
```bash
# 卸载当前版本
pip uninstall torch torchvision torchaudio

# 安装 GPU 版本（CUDA 11.8，兼容性好）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 没有 GPU 的情况
```bash
# 使用 CPU 版本（已经安装）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

## 训练设备选择

### 在任务创建时选择
1. 创建任务时，在"训练设备"下拉框选择：
   - **自动**（推荐）：优先 GPU，不可用时自动降级到 CPU
   - **仅 CPU**：强制使用 CPU
   - **GPU**：强制使用 GPU（如果不可用会降级到 CPU，不会报错）

### 设备降级保护
系统有完善的降级机制：
- ✅ 安装了 GPU 版本但没有 GPU → 自动降级到 CPU
- ✅ 选择了 GPU 但不可用 → 自动降级到 CPU
- ✅ 训练不会报错，只是使用 CPU 运行

## 验证 GPU 是否可用

### 方法 1：使用检测脚本
```bash
python scripts/check_gpu.py
```

### 方法 2：Python 命令
```bash
python -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

### 方法 3：查看训练日志
训练启动时会显示：
- 使用 GPU 训练：NVIDIA GeForce RTX 5060
- 或：使用 CPU 训练（未检测到 GPU）

## 常见问题

### Q: 安装了 GPU 版本但没有 GPU 会怎样？
**答**：会自动降级到 CPU 运行，不会报错。训练可以正常进行，只是速度较慢。

### Q: CPU 版本和 GPU 版本有什么区别？
**答**：
- CPU 版本：可以在任何电脑上运行，速度较慢
- GPU 版本：需要 NVIDIA GPU，训练速度可提升 10-50 倍

### Q: 我的 RTX 5060 支持哪个 CUDA 版本？
**答**：RTX 5060 支持最新的 CUDA 版本。建议使用 CUDA 11.8 版本（兼容性好）。

### Q: 安装 GPU 版本后需要重启吗？
**答**：需要重启 Web 应用才能使用新安装的 GPU 版本 PyTorch。

### Q: 如何确认 GPU 正在被使用？
**答**：
1. 查看训练日志，会显示"使用 GPU 训练：[显卡名称]"
2. 任务管理页面显示 GPU 徽章
3. 使用 `nvidia-smi` 命令查看 GPU 使用情况

## 性能对比

| 设备 | 训练速度 | 适用场景 |
|------|---------|---------|
| RTX 5060 (GPU) | 100% | 推荐，快速训练 |
| CPU (i7 等) | 2-5% | 测试、小数据集 |

**建议**：如果有 GPU，务必安装 GPU 版本 PyTorch，训练速度提升显著。
