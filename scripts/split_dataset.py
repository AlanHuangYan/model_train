#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动拆分数据集为 train/val/test
"""
import json
import os
import random
import argparse

def split_dataset(input_file, output_dir, ratios=(0.8, 0.1, 0.1)):
    """
    将数据集按指定比例拆分
    
    Args:
        input_file: 输入的 JSONL 文件路径
        output_dir: 输出目录
        ratios: (train, val, test) 的比例，默认 80/10/10
    """
    # 读取所有数据
    print(f"读取数据文件：{input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = []
        for line in f:
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"[WARNING] 跳过无效 JSON 行：{e}")
    
    print(f"[OK] 共读取 {len(data)} 条数据")
    
    # 打乱数据
    random.shuffle(data)
    
    # 计算拆分点
    n = len(data)
    train_end = int(n * ratios[0])
    val_end = train_end + int(n * ratios[1])
    
    # 拆分数据
    train_data = data[:train_end]
    val_data = data[train_end:val_end]
    test_data = data[val_end:]
    
    print(f"\n数据拆分：")
    print(f"  - 训练集：{len(train_data)} 条 ({len(train_data)/n*100:.1f}%)")
    print(f"  - 验证集：{len(val_data)} 条 ({len(val_data)/n*100:.1f}%)")
    print(f"  - 测试集：{len(test_data)} 条 ({len(test_data)/n*100:.1f}%)")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存拆分后的文件
    train_file = os.path.join(output_dir, 'train.jsonl')
    val_file = os.path.join(output_dir, 'val.jsonl')
    test_file = os.path.join(output_dir, 'test.jsonl')
    
    # 保存训练集
    with open(train_file, 'w', encoding='utf-8') as f:
        for item in train_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"\n[OK] 保存训练集：{train_file}")
    
    # 保存验证集
    with open(val_file, 'w', encoding='utf-8') as f:
        for item in val_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"[OK] 保存验证集：{val_file}")
    
    # 保存测试集
    with open(test_file, 'w', encoding='utf-8') as f:
        for item in test_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"[OK] 保存测试集：{test_file}")
    
    print(f"\n[OK] 数据集拆分完成！")
    return train_file, val_file, test_file


def cleanup_dataset(output_dir):
    """
    删除临时拆分的数据文件
    """
    import shutil
    print(f"\n清理临时数据文件：{output_dir}")
    try:
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            print(f"[OK] 已删除临时目录：{output_dir}")
        else:
            print(f"[WARNING] 目录不存在，无需清理：{output_dir}")
    except Exception as e:
        print(f"[ERROR] 清理失败：{str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='拆分数据集')
    parser.add_argument('--input_file', type=str, required=True, help='输入的 JSONL 文件')
    parser.add_argument('--output_dir', type=str, required=True, help='输出目录')
    parser.add_argument('--cleanup', action='store_true', help='清理模式：删除临时文件')
    parser.add_argument('--train_ratio', type=float, default=0.8, help='训练集比例（默认 0.8）')
    parser.add_argument('--val_ratio', type=float, default=0.1, help='验证集比例（默认 0.1）')
    parser.add_argument('--test_ratio', type=float, default=0.1, help='测试集比例（默认 0.1）')
    
    args = parser.parse_args()
    
    if args.cleanup:
        cleanup_dataset(args.output_dir)
    else:
        split_dataset(
            args.input_file, 
            args.output_dir,
            ratios=(args.train_ratio, args.val_ratio, args.test_ratio)
        )
