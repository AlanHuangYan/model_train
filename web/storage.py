import os
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class JSONStorage:
    """JSON 文件存储管理"""
    
    def __init__(self, storage_folder):
        self.storage_folder = storage_folder
        os.makedirs(storage_folder, exist_ok=True)
    
    def _get_file_path(self, collection):
        """获取集合文件路径"""
        return os.path.join(self.storage_folder, f"{collection}.json")
    
    def load(self, collection):
        """加载集合数据"""
        file_path = self._get_file_path(collection)
        if not os.path.exists(file_path):
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save(self, collection, data):
        """保存集合数据"""
        file_path = self._get_file_path(collection)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def insert(self, collection, document):
        """插入文档"""
        data = self.load(collection)
        document['_id'] = len(data) + 1
        document['created_at'] = datetime.now().isoformat()
        data.append(document)
        self.save(collection, data)
        return document['_id']
    
    def find(self, collection, query=None):
        """查询文档"""
        data = self.load(collection)
        if query is None:
            return data
        
        # 简单查询支持
        results = []
        for doc in data:
            match = True
            for key, value in query.items():
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                results.append(doc)
        return results
    
    def update(self, collection, doc_id, updates):
        """更新文档"""
        data = self.load(collection)
        for doc in data:
            if doc.get('_id') == doc_id:
                doc.update(updates)
                doc['updated_at'] = datetime.now().isoformat()
                self.save(collection, data)
                return True
        return False
    
    def delete(self, collection, doc_id):
        """删除文档"""
        data = self.load(collection)
        data = [doc for doc in data if doc.get('_id') != doc_id]
        self.save(collection, data)
        return True


# 创建全局存储实例
storage = None


def init_storage(storage_folder):
    """初始化存储"""
    global storage
    storage = JSONStorage(storage_folder)
    return storage
