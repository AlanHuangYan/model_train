from src.trainer import Trainer
from src.result_processor import ResultProcessor
from web.storage import storage
import os


class TrainingService:
    """训练服务"""
    
    def __init__(self):
        self.trainer = Trainer()
        self.result_processor = ResultProcessor()
    
    def execute_task(self, task_id):
        """执行训练任务"""
        # 获取任务信息
        tasks = storage.find('tasks', {'_id': task_id})
        if not tasks:
            return False
        
        task = tasks[0]
        
        # 更新任务状态为运行中
        storage.update('tasks', task_id, {'status': 'running', 'progress': 10})
        
        try:
            # 执行训练
            storage.update('tasks', task_id, {'progress': 30})
            
            # 获取数据文件路径
            data_file = task.get('data_file')
            if data_file:
                data_files = storage.find('data_files', {'filename': data_file})
                if data_files:
                    data_file_path = data_files[0].get('file_path')
                else:
                    data_file_path = None
            else:
                data_file_path = None
            
            # 执行训练
            result = self.trainer.train(data_file_path)
            storage.update('tasks', task_id, {'progress': 80})
            
            # 生成报告
            report_file = self.result_processor.generate_report(result)
            storage.update('tasks', task_id, {'progress': 90})
            
            # 保存模型信息到存储
            model_data = {
                'name': f"Model_v{result['model_version']}",
                'version': result['model_version'],
                'algorithm': result['model_info']['algorithm'],
                'metrics': result['evaluation'],
                'file_path': os.path.join('models', 'current', 'model.joblib'),
                'task_id': task_id
            }
            storage.insert('models', model_data)
            
            # 更新任务结果
            storage.update('tasks', task_id, {
                'status': 'completed',
                'progress': 100,
                'result': result
            })
            
            return True
            
        except Exception as e:
            # 训练失败
            storage.update('tasks', task_id, {
                'status': 'failed',
                'error': str(e)
            })
            return False
