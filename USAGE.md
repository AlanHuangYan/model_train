# 使用示例

## 环境配置

### 1. 创建虚拟环境

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

# 训练依赖（运行训练任务必需）
pip install -r requirements-train.txt
```

### 3. 启动应用

```bash
python run.py
```

### 4. GPU 加速（可选，推荐）

如果有 NVIDIA GPU，建议安装 GPU 版本的 PyTorch 以加速训练：

```bash
# 检测 GPU 状态
python scripts/check_gpu.py

# 自动安装 GPU 版本 PyTorch
python scripts/install_torch.py
```

或在 Web 界面点击"检测 GPU"按钮进行自动检测和安装。

## 快速上手指南

### 1. 第一个训练任务

#### 步骤 1: 注册账号
1. 访问 http://localhost:5000
2. 点击"注册"按钮
3. 填写邮箱和密码
4. 完成注册

#### 步骤 2: 上传数据
1. 进入"数据管理"页面
2. 点击"上传文件"
3. 选择示例数据文件 `data/raw/sample_data.csv`
4. 系统会自动解析并显示数据预览

#### 步骤 3: 创建训练任务
1. 进入"任务管理"页面
2. 点击"新建任务"
3. 填写信息：
   - 任务名称：`我的第一个训练任务`
   - 数据文件：选择刚上传的 `sample_data.csv`
   - 模型类型：选择`分类`
4. 点击"创建任务"

#### 步骤 4: 查看结果
1. 任务状态变为"已完成"后，点击"查看"
2. 查看训练结果和评估指标
3. 进入"模型管理"查看训练好的模型

### 2. 使用 API

#### Python 示例

```python
import requests

# 登录获取会话
session = requests.Session()

# 登录
login_data = {
    'email': 'your@email.com',
    'password': 'your_password'
}
response = session.post('http://localhost:5000/login', data=login_data)

# 创建任务
task_data = {
    'name': 'API 创建的任务',
    'data_file': 'sample_data.csv',
    'model_type': 'classification'
}
response = session.post('http://localhost:5000/api/tasks', json=task_data)
task_id = response.json()['id']

# 查看任务状态
response = session.get(f'http://localhost:5000/api/tasks/{task_id}')
print(response.json())

# 获取模型列表
response = session.get('http://localhost:5000/api/models')
print(response.json())
```

#### cURL 示例

```bash
# 登录（需要处理 Cookie）
curl -X POST http://localhost:5000/login \
  -d "email=your@email.com" \
  -d "password=your_password" \
  -c cookies.txt

# 创建任务
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"name":"API 任务","data_file":"sample_data.csv","model_type":"classification"}'

# 获取任务列表
curl -X GET http://localhost:5000/api/tasks \
  -b cookies.txt
```

### 3. 数据格式要求

#### CSV 文件格式

```csv
feature1,feature2,feature3,target
1.0,2.0,3.0,0
2.0,3.0,4.0,1
3.0,4.0,5.0,1
```

- 最后一列默认为目标列（target）
- 其他列为特征列
- 支持数值型和分类型数据

#### JSON 文件格式

```json
[
  {"feature1": 1.0, "feature2": 2.0, "target": 0},
  {"feature1": 2.0, "feature2": 3.0, "target": 1}
]
```

### 4. 模型类型说明

#### 分类 (classification)
- 适用于预测离散类别
- 示例算法：逻辑回归、决策树、随机森林
- 评估指标：准确率、精确率、召回率

#### 回归 (regression)
- 适用于预测连续数值
- 示例算法：线性回归、岭回归
- 评估指标：MSE、MAE、R²

#### 聚类 (clustering)
- 适用于无监督分组
- 示例算法：K-Means、DBSCAN
- 评估指标：轮廓系数、惯性

### 5. 最佳实践

#### 数据准备
- 确保数据质量（无缺失值、异常值）
- 特征工程（标准化、归一化）
- 数据集划分（训练集/测试集）

#### 模型训练
- 从小数据集开始测试
- 逐步增加数据量
- 保存重要版本的模型

#### 任务管理
- 使用描述性的任务名称
- 定期清理已完成的任务
- 监控任务执行状态

### 6. 故障排除

#### 问题：无法登录
- 检查邮箱和密码是否正确
- 清除浏览器缓存
- 重启应用

#### 问题：数据上传失败
- 检查文件格式（CSV 或 JSON）
- 确认文件大小（< 16MB）
- 检查目录权限

#### 问题：训练任务失败
- 查看任务详情中的错误信息
- 确认数据文件格式正确
- 检查日志文件

### 7. GPU 加速训练

#### 检测 GPU 状态
在任务管理页面点击"检测 GPU"按钮，系统会显示：
- NVIDIA GPU 信息
- CUDA 版本
- PyTorch CUDA 支持情况
- 推荐安装方案

#### 安装 GPU 版本 PyTorch
```bash
python scripts/install_torch.py
```

或在 Web 界面点击"安装 GPU 版本 PyTorch"按钮。

#### 选择训练设备
创建任务时，在"训练设备"下拉框选择：
- **自动**（推荐）：优先使用 GPU，不可用时自动降级到 CPU
- **仅 CPU**：强制使用 CPU 训练
- **GPU**：强制使用 GPU（如果不可用会降级到 CPU，不会报错）

#### 降级保护
系统有完善的降级机制：
- ✅ 安装了 GPU 版本但没有 GPU → 自动降级到 CPU
- ✅ 选择了 GPU 但不可用 → 自动降级到 CPU
- ✅ 训练不会报错，只是使用 CPU 运行

详见 [GPU_GUIDE.md](GPU_GUIDE.md)

### 8. 训练任务说明

训练任务会使用虚拟环境中安装的依赖，包括：
- `torch` - PyTorch 深度学习框架
- `transformers` - Hugging Face transformers 库
- `peft` - 参数高效微调库
- `datasets` - 数据集处理库
- `accelerate` - 训练加速库
- `bitsandbytes` - 量化库

训练日志会保存在 `logs/task_{task_id}.log` 和 `logs/task_{task_id}_train.log` 文件中，可以通过任务详情页面查看。

### 8. 高级用法

#### 批量创建任务

```python
import requests

session = requests.Session()
# 登录后...

# 批量创建任务
for i in range(5):
    task_data = {
        'name': f'批量任务_{i}',
        'data_file': 'sample_data.csv',
        'model_type': 'classification'
    }
    response = session.post('http://localhost:5000/api/tasks', json=task_data)
    print(f"任务{i}创建成功：{response.json()['id']}")
```

#### 导出模型

```python
import requests

session = requests.Session()
# 登录后...

# 获取模型列表
response = session.get('http://localhost:5000/api/models')
models = response.json()

# 下载模型
model_id = models[0]['_id']
response = session.get(f'http://localhost:5000/models/{model_id}/download')

with open('model.joblib', 'wb') as f:
    f.write(response.content)
```
