#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检测系统 GPU 和 PyTorch CUDA 支持情况
"""
import sys
import subprocess
import importlib

# 修复 Windows 编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_nvidia_smi():
    """检查 NVIDIA 驱动"""
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            # 解析 GPU 信息
            for line in result.stdout.split('\n'):
                if 'NVIDIA' in line and 'Driver Version' in line:
                    return True, line.strip()
            return True, "NVIDIA 驱动正常"
        return False, "nvidia-smi 命令失败"
    except FileNotFoundError:
        return False, "未找到 nvidia-smi 命令"
    except Exception as e:
        return False, f"检查失败：{str(e)}"

def check_cuda_version():
    """检查 CUDA 版本"""
    try:
        result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'release' in line:
                    return True, line.strip()
            return True, "CUDA 已安装"
        return False, "nvcc 命令失败"
    except FileNotFoundError:
        return False, "未找到 nvcc 命令"
    except Exception as e:
        return False, f"检查失败：{str(e)}"

def check_pytorch_cuda():
    """检查 PyTorch CUDA 支持"""
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "未知"
            return True, f"CUDA 可用，{gpu_count} 个 GPU: {gpu_name}"
        else:
            # 检查 PyTorch 版本
            version = torch.__version__
            if '+cpu' in version:
                return False, f"PyTorch {version} 是 CPU 版本"
            else:
                return False, f"PyTorch {version} 未检测到 GPU"
    except ImportError:
        return False, "PyTorch 未安装"
    except Exception as e:
        return False, f"检查失败：{str(e)}"

def get_recommended_install():
    """获取推荐的安装命令"""
    has_gpu, gpu_info = check_nvidia_smi()
    has_cuda, cuda_info = check_cuda_version()
    
    if has_gpu:
        # 有 GPU，推荐安装 GPU 版本
        print("\n[OK] 检测到 NVIDIA GPU")
        print(f"   {gpu_info}")
        if has_cuda:
            print(f"   CUDA: {cuda_info}")
        else:
            print("   [WARNING] 未检测到 CUDA Toolkit（可选）")
        
        print("\n[INFO] 推荐安装 GPU 版本的 PyTorch:")
        print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
        return "gpu"
    else:
        # 没有 GPU
        print("\n[INFO] 未检测到 NVIDIA GPU")
        print("   系统将使用 CPU 进行训练")
        print("\n[INFO] 当前 CPU 版本的 PyTorch 已经足够")
        return "cpu"

def main():
    print("=" * 60)
    print("GPU 和 PyTorch CUDA 支持检测")
    print("=" * 60)
    
    # 检查 NVIDIA 驱动
    has_gpu, gpu_info = check_nvidia_smi()
    print(f"\n[NVIDIA 驱动:]")
    print(f"   {'[OK]' if has_gpu else '[FAIL]'} {gpu_info}")
    
    # 检查 CUDA
    has_cuda, cuda_info = check_cuda_version()
    print(f"\n[CUDA Toolkit:]")
    print(f"   {'[OK]' if has_cuda else '[FAIL]'} {cuda_info}")
    
    # 检查 PyTorch
    pytorch_cuda, pytorch_info = check_pytorch_cuda()
    print(f"\n[PyTorch CUDA 支持:]")
    print(f"   {'[OK]' if pytorch_cuda else '[FAIL]'} {pytorch_info}")
    
    # 推荐安装
    print("\n" + "=" * 60)
    get_recommended_install()
    print("=" * 60)

if __name__ == "__main__":
    main()
