#!/usr/bin/env python3
"""
权限检查工具
检查 Web 应用是否有足够的权限运行训练任务
"""

import os
import sys
from pathlib import Path

def check_permission(path, permission):
    """检查指定路径的权限"""
    try:
        if permission == 'read':
            if os.path.isfile(path):
                with open(path, 'r', encoding='utf-8') as f:
                    f.read(1)
                return True, "可读"
            elif os.path.isdir(path):
                os.listdir(path)
                return True, "可读取目录"
        elif permission == 'write':
            if os.path.isdir(path):
                test_file = os.path.join(path, '.permission_test')
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write('test')
                os.remove(test_file)
                return True, "可写入"
            else:
                # 目录不存在，尝试创建
                parent = os.path.dirname(path)
                if os.path.isdir(parent):
                    os.makedirs(path, exist_ok=True)
                    return True, "可创建目录"
                return False, "父目录不存在"
        elif permission == 'execute':
            if os.path.isfile(path):
                os.access(path, os.X_OK)
                return True, "可执行"
        return False, "未知权限类型"
    except PermissionError as e:
        return False, f"权限错误：{str(e)}"
    except Exception as e:
        return False, f"检查失败：{str(e)}"

def main():
    """主函数"""
    base_dir = Path(__file__).parent
    
    print("=" * 60)
    print("权限检查工具")
    print("=" * 60)
    print(f"项目根目录：{base_dir}")
    print(f"Python 版本：{sys.version}")
    print(f"当前用户：{os.getenv('USERNAME' if os.name == 'nt' else 'USER')}")
    print("=" * 60)
    print()
    
    # 检查项目
    checks = [
        ("日志目录", base_dir / "logs", "write"),
        ("模型目录", base_dir / "models", "write"),
        ("训练脚本", base_dir / "scripts" / "train_model.py", "read"),
        ("数据目录", base_dir / "data", "write"),
        ("Web 目录", base_dir / "web", "read"),
    ]
    
    all_passed = True
    
    for name, path, permission in checks:
        exists = "[OK] 存在" if os.path.exists(path) else "[FAIL] 不存在"
        passed, message = check_permission(path, permission)
        status = "[OK] 通过" if passed else "[FAIL] 失败"
        
        print(f"{name}:")
        print(f"  路径：{path}")
        print(f"  状态：{exists}")
        print(f"  权限 ({permission}): {message} - {status}")
        print()
        
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("[OK] 所有权限检查通过！可以正常运行训练任务。")
    else:
        print("[FAIL] 部分权限检查失败！请修复以下问题：")
        print()
        print("解决方案：")
        print("1. 右键点击项目根目录 → 属性 → 安全")
        print("2. 确保当前用户有'完全控制'或'修改'权限")
        print("3. 如果是 Windows，可能需要以管理员身份运行")
        print("4. 如果是 Linux/Mac，使用 chmod 命令修改权限")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
