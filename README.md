# 模型训练管理系统

一个通用的模型训练 Web 管理系统，支持模型设定、新数据训练、定期训练和多任务排队执行。

## 功能特性

### 核心功能
- ✅ **用户认证系统** - 支持用户注册、登录、权限管理
- ✅ **仪表板** - 系统状态概览、任务统计、最近活动
- ✅ **任务管理** - 创建、查看、删除、取消训练任务
- ✅ **模型管理** - 模型列表、详情查看、文件下载、版本管理
- ✅ **数据管理** - 数据上传、预览、删除、CSV 自动解析
- ✅ **RESTful API** - 完整的 API 接口支持
- ✅ **训练集成** - 与后台训练系统无缝集成
- ✅ **模型对比测试** - Base 模型与合并模型实时对比，支持思考过程展示

### 待实现功能 (TODO)
- 🔮 模型预测功能 - 用户上传测试数据并进行预测
- 📊 实验跟踪 - 记录训练参数和结果，支持对比分析
- 📈 数据可视化 - 数据分布图、特征相关性热力图
- ⚙️ 超参数调优 - 网格搜索和随机搜索
- 🚀 模型导出 - 导出为 ONNX、PMML 等格式
- 📱 高级监控 - 性能监控、数据漂移检测
- 📄 报告生成 - 自动生成 PDF/HTML 报告

## 技术栈

- **后端框架**: Flask 3.1+
- **认证**: Flask-Login
- **表单**: Flask-WTF
- **数据存储**: JSON 文件
- **前端**: Bootstrap 5, Bootstrap Icons
- **模型推理**: Transformers, PyTorch, bitsandbytes (4bit 量化)
- **数据处理**: Pandas, scikit-learn
- **测试**: pytest

## 快速开始

### 1. 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. 安装依赖

```bash
# Web 应用依赖
pip install -r requirements-web.txt

# 训练依赖（如果需要运行训练任务）
pip install -r requirements-train.txt
```

### 3. 安装训练依赖

```bash
# 训练依赖（如果需要运行训练任务）
pip install -r requirements-train.txt
```

### 4. GPU 加速（可选，推荐）

如果有 NVIDIA GPU，可以安装 GPU 版本的 PyTorch 以加速训练：

```bash
# 检测 GPU 状态
python scripts/check_gpu.py

# 自动安装 GPU 版本 PyTorch
python scripts/install_torch.py
```

或在 Web 界面点击"检测 GPU"按钮进行自动检测和安装。

### 5. 启动应用

确保在虚拟环境中运行：

```bash
python run.py
```

应用将在 http://localhost:5000 运行

### 6. 访问系统

1. 访问 http://localhost:5000
2. 点击"注册"创建账号
3. 登录后即可使用所有功能

## 项目结构

```
model_train/
├── web/                          # Web 应用
│   ├── __init__.py              # Flask 应用工厂
│   ├── config.py                # 配置管理
│   ├── extensions.py            # Flask 扩展
│   ├── storage.py               # JSON 存储管理
│   │
│   ├── auth/                    # 认证模块
│   ├── dashboard/               # 仪表板
│   ├── tasks/                   # 任务管理
│   ├── models/                  # 模型管理
│   ├── data/                    # 数据管理
│   ├── api/                     # API 接口
│   ├── services/                # 服务层
│   └── templates/               # HTML 模板
│
├── src/                         # 训练系统核心
├── data/raw/                    # 原始数据
├── models/                      # 模型文件
├── storage/                     # JSON 数据文件
├── tests/                       # 测试文件
├── docs/                        # 文档
├── scripts/                     # 工具脚本
│   ├── check_gpu.py            # GPU 检测脚本
│   ├── install_torch.py        # PyTorch 自动安装脚本
│   └── train_model.py          # 模型训练脚本
├── requirements-web.txt         # Web 依赖
├── requirements-train.txt       # 训练依赖
└── run.py                       # 应用入口
```

## 使用指南

### 上传数据

1. 进入"数据管理"页面
2. 点击"上传文件"
3. 选择 CSV 或 JSON 格式的数据文件
4. 系统会自动解析并显示数据预览

### 创建训练任务

1. 进入"任务管理"页面
2. 点击"新建任务"
3. 填写任务名称、选择数据文件和模型类型
4. 提交后任务将进入队列等待执行

### 查看模型

1. 进入"模型管理"页面
2. 查看已训练的模型列表
3. 点击"查看"查看模型详情和评估指标
4. 点击"下载"下载模型文件

### 模型对比测试

1. 进入任务详情页面
2. 点击"对比测试"进入对比页面
3. 输入问题，设置参数（最大生成长度、温度、深度思考）
4. 点击"发送对比"，同时推理 Base 模型和合并模型
5. 查看两个模型的回答差异，思考过程可点击展开查看
6. 历史记录会自动保存，方便后续对比分析

## API 接口

### 任务管理 API

```bash
# 获取任务列表
GET /api/tasks

# 创建任务
POST /api/tasks
{
  "name": "任务名称",
  "data_file": "数据文件名",
  "model_type": "classification"
}

# 获取任务详情
GET /api/tasks/<task_id>

# 更新任务状态
PUT /api/tasks/<task_id>
{
  "status": "running",
  "progress": 50
}
```

### 模型管理 API

```bash
# 获取模型列表
GET /api/models

# 获取数据文件列表
GET /api/data
```

所有 API 端点都需要登录后才能访问。

## 测试

运行测试：

```bash
pytest tests/test_web.py -v
```

## 配置

配置文件位于 `web/config.py`，支持以下配置：

- `SECRET_KEY`: Flask 密钥
- `UPLOAD_FOLDER`: 上传文件目录
- `STORAGE_FOLDER`: JSON 存储目录
- `MODEL_FOLDER`: 模型文件目录
- `MAX_CONTENT_LENGTH`: 最大上传文件大小（16MB）

### 环境配置

可以通过环境变量覆盖默认配置：

```bash
export SECRET_KEY=your-secret-key
export FLASK_ENV=production
```

## 开发

### 添加新功能

1. 在对应的 blueprint 目录下创建路由文件
2. 在 `__init__.py` 中注册蓝图
3. 创建对应的 HTML 模板
4. 添加测试用例

### 代码规范

- 遵循 PEP 8 编码规范
- 使用类型提示
- 编写单元测试
- 保持函数简洁（单一职责）

## 常见问题

### Q: 如何修改默认端口？

编辑 `run.py` 文件：

```python
app.run(debug=True, host='0.0.0.0', port=5001)  # 修改 port 参数
```

### Q: 数据文件上传失败？

检查：
1. 文件格式是否为 CSV 或 JSON
2. 文件大小是否超过 16MB
3. `data/raw` 目录是否有写入权限

### Q: 训练任务执行失败？

检查：
1. 数据文件是否存在
2. 数据格式是否正确
3. 查看系统日志获取详细错误信息
4. 确认已安装训练依赖：`pip install -r requirements-train.txt`

### Q: 为什么需要使用虚拟环境？

虚拟环境可以：
- 隔离项目依赖，不影响全局 Python 环境
- 避免不同项目之间的版本冲突
- 方便管理和部署

### Q: ModuleNotFoundError: No module named 'peft'

这是因为缺少训练依赖。请运行：

```bash
pip install -r requirements-train.txt
```

或者检查是否在虚拟环境中运行。

### Q: 如何使用 GPU 加速训练？

1. **检测 GPU**：在任务管理页面点击"检测 GPU"按钮
2. **安装 GPU 版本 PyTorch**：
   ```bash
   python scripts/install_torch.py
   ```
3. **创建任务时选择 GPU**：在"训练设备"下拉框选择"自动"或"GPU"
4. **查看训练日志**：会显示"使用 GPU 训练：[显卡名称]"

详见 [GPU_GUIDE.md](GPU_GUIDE.md)

### Q: 安装了 GPU 版本但没有 GPU 会怎样？

系统会自动降级到 CPU 运行，不会报错。训练可以正常进行，只是速度较慢。

训练脚本有完善的降级保护机制：
- 指定 GPU 但不可用时 → 自动降级到 CPU
- 不会报错，只是打印警告信息
- 训练任务可以正常完成

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 联系方式

如有问题，请通过 Issue 系统反馈。
