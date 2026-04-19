# -*- coding: utf-8 -*-
"""
模型缓存管理器

负责模型的加载、缓存和推理。
支持 GPU (4bit 量化) 和 CPU 两种模式，自动检测并切换。
"""
import os
import json
import time
import threading
from datetime import datetime


def _log(message, level='INFO'):
    """日志输出"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] [{level}] [ModelCache] {message}')


class ModelCache:
    """
    模型缓存管理器

    - 简单缓存策略：模型加载后保留在内存中，不主动卸载
    - GPU 可用时使用 4bit 量化加载，节省显存
    - GPU 不可用时使用 CPU 加载
    - 线程安全：使用锁避免并发加载冲突
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式，全局共享一个缓存实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 模型缓存：{model_path: {'model': ..., 'tokenizer': ..., 'loaded_at': ...}}
        self._cache = {}

        # 加载锁，防止同一个模型被并发加载
        self._load_locks = {}
        self._global_lock = threading.Lock()

        # 检测 GPU 是否可用
        self._gpu_available = self._detect_gpu()
        _log(f'GPU 可用: {self._gpu_available}')

        # 检测 bitsandbytes 是否可用（用于 4bit 量化）
        self._bnb_available = self._detect_bnb()
        _log(f'bitsandbytes 可用: {self._bnb_available}')

    def _detect_gpu(self):
        """检测 GPU 是否可用"""
        try:
            import torch
            available = torch.cuda.is_available()
            if available:
                device_name = torch.cuda.get_device_name(0)
                _log(f'检测到 GPU: {device_name}')
            else:
                _log('未检测到 GPU，将使用 CPU 模式')
            return available
        except Exception as e:
            _log(f'检测 GPU 时出错: {e}', 'WARNING')
            return False

    def _detect_bnb(self):
        """检测 bitsandbytes 是否可用"""
        try:
            import bitsandbytes  # noqa: F401
            _log('bitsandbytes 已安装，支持 4bit 量化')
            return True
        except ImportError:
            _log('bitsandbytes 未安装，不支持 4bit 量化', 'WARNING')
            return False

    def get_device_info(self):
        """获取当前设备信息，供前端展示"""
        info = {
            'gpu_available': self._gpu_available,
            'bnb_available': self._bnb_available,
            'mode': 'unknown',
            'device_name': 'CPU',
        }

        if self._gpu_available and self._bnb_available:
            info['mode'] = 'gpu_4bit'
            try:
                import torch
                info['device_name'] = torch.cuda.get_device_name(0)
                info['vram_total_gb'] = round(torch.cuda.get_device_properties(0).total_mem / (1024**3), 1)
            except Exception:
                pass
        elif self._gpu_available:
            info['mode'] = 'gpu_fp16'
            try:
                import torch
                info['device_name'] = torch.cuda.get_device_name(0)
            except Exception:
                pass
        else:
            info['mode'] = 'cpu'

        return info

    def get_model(self, model_path):
        """
        获取模型（从缓存加载或新加载）

        Args:
            model_path: 模型路径

        Returns:
            dict: {'model': ..., 'tokenizer': ...}
        """
        # 检查缓存
        if model_path in self._cache:
            _log(f'从缓存获取模型: {model_path}')
            return self._cache[model_path]

        # 获取该模型的加载锁（防止并发加载同一个模型）
        with self._global_lock:
            if model_path not in self._load_locks:
                self._load_locks[model_path] = threading.Lock()
            load_lock = self._load_locks[model_path]

        # 加载模型（加锁）
        with load_lock:
            # 双重检查
            if model_path in self._cache:
                _log(f'从缓存获取模型（双重检查）: {model_path}')
                return self._cache[model_path]

            _log(f'开始加载模型: {model_path}')
            start_time = time.time()

            try:
                model, tokenizer = self._load_model(model_path)

                elapsed = time.time() - start_time
                _log(f'模型加载完成: {model_path} (耗时 {elapsed:.1f}s)')

                # 存入缓存
                self._cache[model_path] = {
                    'model': model,
                    'tokenizer': tokenizer,
                    'loaded_at': datetime.now().isoformat(),
                    'load_time': elapsed,
                }

                return self._cache[model_path]

            except Exception as e:
                _log(f'加载模型失败: {model_path}, 错误: {e}', 'ERROR')
                raise

    def _load_model(self, model_path):
        """
        加载模型和 tokenizer

        根据 GPU 可用性自动选择加载方式：
        - GPU + bitsandbytes: 4bit 量化加载
        - GPU (无 bnb): FP16 加载
        - CPU: 普通加载
        """
        from transformers import AutoModelForCausalLM, AutoTokenizer

        # 检查模型路径是否存在
        if not os.path.exists(model_path):
            raise FileNotFoundError(f'模型路径不存在: {model_path}')

        # 读取 config.json 判断是否为多模态模型
        config_path = os.path.join(model_path, 'config.json')
        is_multimodal = False
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            is_multimodal = 'vision_config' in config_dict or 'image_token_id' in config_dict

        if is_multimodal:
            _log(f'检测到多模态模型，将只加载文本部分: {model_path}')

        # 加载 tokenizer
        _log(f'加载 tokenizer: {model_path}')
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )

        # 根据 GPU 可用性选择加载方式
        if self._gpu_available and self._bnb_available:
            # GPU + 4bit 量化
            _log(f'使用 GPU 4bit 量化加载模型: {model_path}')
            from transformers import BitsAndBytesConfig

            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype='float16',
                bnb_4bit_quant_type='nf4',
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                quantization_config=quantization_config,
                device_map='auto',
                trust_remote_code=True,
            )

        elif self._gpu_available:
            # GPU + FP16
            _log(f'使用 GPU FP16 加载模型: {model_path}')
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype='auto',
                device_map='auto',
                trust_remote_code=True,
            )

        else:
            # CPU 模式
            _log(f'使用 CPU 加载模型: {model_path}')
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=True,
            )

        # 设置为评估模式
        model.eval()
        _log(f'模型已设置为评估模式: {model_path}')

        return model, tokenizer

    def generate(self, model_path, prompt, max_new_tokens=512, temperature=0.7):
        """
        使用指定模型生成回答

        Args:
            model_path: 模型路径
            prompt: 输入提示
            max_new_tokens: 最大生成 token 数
            temperature: 采样温度

        Returns:
            str: 模型生成的文本
        """
        _log(f'开始推理: model={model_path}, prompt长度={len(prompt)}')

        # 获取模型
        cached = self.get_model(model_path)
        model = cached['model']
        tokenizer = cached['tokenizer']

        start_time = time.time()

        try:
            import torch

            # 编码输入
            inputs = tokenizer(prompt, return_tensors='pt')

            # 将输入移到模型所在设备
            device = next(model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}

            # 生成
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=temperature > 0,
                    top_p=0.9,
                    pad_token_id=tokenizer.eos_token_id,
                )

            # 解码输出（只取新生成的部分）
            input_length = inputs['input_ids'].shape[1]
            generated_ids = outputs[0][input_length:]
            response = tokenizer.decode(generated_ids, skip_special_tokens=True)
            
            # 清理 Qwen 模型的思考标签（<think></think>）
            # 这些标签在 tokenizer 中不是 special tokens，需要手动清理
            response = response.replace('<think>', '').replace('</think>', '')
            
            elapsed = time.time() - start_time
            _log(f'推理完成：model={model_path}, 耗时={elapsed:.1f}s, 生成长度={len(generated_ids)}')
            
            return response.strip()

        except Exception as e:
            elapsed = time.time() - start_time
            _log(f'推理失败: model={model_path}, 耗时={elapsed:.1f}s, 错误={e}', 'ERROR')
            raise

    def is_model_loaded(self, model_path):
        """检查模型是否已缓存"""
        return model_path in self._cache

    def get_cached_models(self):
        """获取当前缓存的所有模型信息"""
        result = {}
        for path, info in self._cache.items():
            result[path] = {
                'loaded_at': info['loaded_at'],
                'load_time': round(info['load_time'], 1),
            }
        return result

    def unload_model(self, model_path):
        """卸载指定模型，释放内存"""
        if model_path not in self._cache:
            _log(f'模型不在缓存中，无需卸载: {model_path}')
            return

        _log(f'卸载模型: {model_path}')
        try:
            import torch
            cached = self._cache.pop(model_path)
            model = cached['model']
            del model

            # 尝试释放 GPU 显存
            if self._gpu_available:
                torch.cuda.empty_cache()
                _log('已释放 GPU 显存')

        except Exception as e:
            _log(f'卸载模型时出错: {e}', 'WARNING')

    def clear_cache(self):
        """清空所有模型缓存"""
        _log(f'清空所有模型缓存，共 {len(self._cache)} 个模型')
        paths = list(self._cache.keys())
        for path in paths:
            self.unload_model(path)


# 全局单例
model_cache = ModelCache()
