#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动检测并安装合适的 PyTorch 版本
"""
import sys
import subprocess
import os

# 修复 Windows 编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def check_nvidia_gpu():
    """检查是否有 NVIDIA GPU"""
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def get_current_torch_version():
    """获取当前 PyTorch 版本"""
    try:
        import torch
        return torch.__version__
    except:
        return None

def get_recommended_install():
    """获取推荐的安装命令"""
    has_gpu = check_nvidia_gpu()
    
    if has_gpu:
        # 检测 GPU 型号
        try:
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
            gpu_info = result.stdout if result.returncode == 0 else ''
            is_rtx_5060 = '5060' in gpu_info or 'RTX 50' in gpu_info
        except:
            is_rtx_5060 = False
        
        # 有 GPU，推荐安装 GPU 版本
        print("\n[OK] 检测到 NVIDIA GPU")
        if is_rtx_5060:
            print("\n[INFO] RTX 5060 显卡需要 CUDA 12.4 或更高版本支持")
            print("\n推荐安装方式（二选一）：")
            print("\n方式 1: 使用 pip 安装（推荐）")
            print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124")
            print("\n方式 2: 使用 nightly 版本（最新，支持更好）")
            print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128")
            print("\n[NOTE] RTX 5060 需要 CUDA 12.4 或更高版本！")
            return "gpu_5060"
        else:
            print("\n[INFO] 推荐安装 GPU 版本的 PyTorch:")
            print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124")
            print("\n   对于 30XX/40XX 显卡，需要 CUDA 11.1 以上版本")
            print("   对于 50XX 显卡，需要 CUDA 12.4 以上版本")
        return "gpu"
    else:
        # 没有 GPU
        print("\n[INFO] 未检测到 NVIDIA GPU")
        print("   系统将使用 CPU 进行训练")
        print("\n[INFO] 当前 CPU 版本的 PyTorch 已经足够")
        return "cpu"

def install_gpu_torch():
    """安装 GPU 版本的 PyTorch"""
    print("正在安装 GPU 版本的 PyTorch...")
    print("CUDA 12.4 版本（兼容新显卡如 RTX 5060）...")
    
    cmd = [
        sys.executable, '-m', 'pip', 'install',
        'torch', 'torchvision', 'torchaudio',
        '--index-url', 'https://download.pytorch.org/whl/cu124',
        '--upgrade'
    ]
    
    # 在 Windows 上设置环境变量以使用 UTF-8 编码
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    result = subprocess.run(cmd, env=env)
    
    if result.returncode == 0:
        print("\n[OK] GPU 版本 PyTorch 安装成功！")
        print("请重启应用后重试训练任务")
        return True
    else:
        print("\n[ERROR] 安装失败，请手动执行以下命令:")
        print("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
        return False

def install_cpu_torch():
    """安装 CPU 版本的 PyTorch"""
    print("正在安装 CPU 版本的 PyTorch...")
    
    cmd = [
        sys.executable, '-m', 'pip', 'install',
        'torch', 'torchvision', 'torchaudio',
        '--index-url', 'https://download.pytorch.org/whl/cpu',
        '--upgrade'
    ]
    
    # 在 Windows 上设置环境变量以使用 UTF-8 编码
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    result = subprocess.run(cmd, env=env)
    
    if result.returncode == 0:
        print("\n[OK] CPU 版本 PyTorch 安装成功！")
        return True
    else:
        print("\n[ERROR] 安装失败")
        return False

def main():
    print("=" * 60)
    print("PyTorch 自动安装工具")
    print("=" * 60)
    
    has_gpu = check_nvidia_gpu()
    current_version = get_current_torch_version()
    
    print(f"\n当前 PyTorch 版本：{current_version or '未安装'}")
    print(f"系统 GPU 状态：{'有 NVIDIA GPU' if has_gpu else '无 GPU'}")
    
    if has_gpu:
        print("\n检测到 NVIDIA GPU，建议安装 GPU 版本")
        print("GPU 版本可以显著加速训练过程")
        print("\n是否安装 GPU 版本的 PyTorch?")
        print("1. 安装 GPU 版本（推荐）")
        print("2. 保持当前 CPU 版本")
        print("3. 退出")
        
        choice = input("\n请选择 [1-3]: ").strip()
        
        if choice == '1':
            install_gpu_torch()
        elif choice == '2':
            print("保持 CPU 版本，训练速度会较慢")
        else:
            print("已退出")
    else:
        print("\n未检测到 GPU，将使用 CPU 版本")
        print("CPU 版本可以进行训练，但速度较慢")
        
        if current_version and '+cpu' not in current_version:
            print("\n当前版本可能不是纯 CPU 版本，是否重新安装？")
            choice = input("重新安装 CPU 版本？[y/n]: ").strip().lower()
            if choice == 'y':
                install_cpu_torch()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
