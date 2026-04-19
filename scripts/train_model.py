#!/usr/bin/env python3
"""
酒店客服模型训练脚本
基于 Qwen3.5-0.8B 使用 LoRA 进行微调
"""

import json
import argparse
from pathlib import Path
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType
)
from datasets import Dataset
import torch

def load_jsonl_data(filepath):
    """加载 JSONL 格式数据"""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def format_instruction(example):
    """格式化指令数据为训练文本"""
    text = f"""### Instruction:
{example['instruction']}

### Response:
{example['output']}"""
    
    if example.get('input'):
        text = f"""### Instruction:
{example['instruction']}

### Input:
{example['input']}

### Response:
{example['output']}"""
    
    return {"text": text}

def main():
    parser = argparse.ArgumentParser(description='训练酒店客服模型')
    parser.add_argument('--data_dir', type=str, default='data/hotel_customer_service',
                       help='训练数据目录')
    parser.add_argument('--output_dir', type=str, default='models/hotel_cs_lora',
                       help='模型输出目录')
    parser.add_argument('--base_model', type=str, default='Qwen/Qwen3.5-0.8B',
                       help='基础模型名称或路径')
    parser.add_argument('--epochs', type=int, default=3, help='训练轮数')
    parser.add_argument('--batch_size', type=int, default=4, help='批次大小')
    parser.add_argument('--lr', type=float, default=2e-4, help='学习率')
    parser.add_argument('--lora_r', type=int, default=8, help='LoRA rank')
    parser.add_argument('--lora_alpha', type=int, default=16, help='LoRA alpha')
    parser.add_argument('--max_length', type=int, default=512, help='最大序列长度')
    parser.add_argument('--use_4bit', action='store_true', help='使用 4bit 量化')
    parser.add_argument('--use_gpu', type=str, default='auto', choices=['auto', 'cpu', 'gpu'],
                       help='训练设备选择：auto(自动), cpu(仅 CPU), gpu(仅 GPU)')
    parser.add_argument('--merge_model', action='store_true', help='训练完成后合并 LoRA 权重到基础模型')
    parser.add_argument('--task_id', type=int, help='任务 ID（用于更新状态）')
    
    args = parser.parse_args()
    
    # 根据参数设置设备（带降级保护）
    if args.use_gpu == 'cpu':
        device = 'cpu'
        print(f"使用 CPU 训练")
    elif args.use_gpu == 'gpu':
        if torch.cuda.is_available():
            device = 'cuda'
            print(f"使用 GPU 训练：{torch.cuda.get_device_name(0)}")
        else:
            # 降级到 CPU，不报错
            device = 'cpu'
            print("[WARNING] 指定使用 GPU 但未检测到 CUDA 设备，降级到 CPU 训练")
            print("   如需使用 GPU，请安装 GPU 版本的 PyTorch:")
            print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
    else:  # auto
        if torch.cuda.is_available():
            device = 'cuda'
            print(f"自动选择：使用 GPU 训练：{torch.cuda.get_device_name(0)}")
        else:
            device = 'cpu'
            print("自动选择：使用 CPU 训练（未检测到 GPU）")
    
    print(f"加载数据 from {args.data_dir}...")
    
    # 检查是否需要拆分数据（如果 data_dir 是临时目录）
    if args.data_dir.endswith('_temp'):
        print(f"[INFO] 检测到临时数据目录，将在训练后清理")
    
    # 加载数据
    train_data = load_jsonl_data(Path(args.data_dir) / 'train.jsonl')
    val_data = load_jsonl_data(Path(args.data_dir) / 'val.jsonl')
    
    print(f"训练集：{len(train_data)} 条")
    print(f"验证集：{len(val_data)} 条")
    
    # 转换为 Dataset
    train_dataset = Dataset.from_list(train_data)
    val_dataset = Dataset.from_list(val_data)
    
    # 格式化
    train_dataset = train_dataset.map(format_instruction)
    val_dataset = val_dataset.map(format_instruction)
    
    print("加载 tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    
    print(f"加载基础模型：{args.base_model}...")
    
    # 根据设备设置加载模型
    if device == 'cpu':
        # CPU 模式
        model = AutoModelForCausalLM.from_pretrained(
            args.base_model,
            trust_remote_code=True
        )
    else:
        # GPU 模式
        if args.use_4bit:
            model = AutoModelForCausalLM.from_pretrained(
                args.base_model,
                load_in_4bit=True,
                device_map="auto",
                trust_remote_code=True
            )
            model = prepare_model_for_kbit_training(model)
        else:
            model = AutoModelForCausalLM.from_pretrained(
                args.base_model,
                device_map="auto",
                trust_remote_code=True
            )
    
    # 配置 LoRA
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        inference_mode=False,
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=0.1,
        target_modules=["q_proj", "v_proj"]  # 根据模型结构调整
    )
    
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()
    
    # Tokenize
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=args.max_length,
            padding="max_length"
        )
    
    train_dataset = train_dataset.map(tokenize_function, batched=True)
    val_dataset = val_dataset.map(tokenize_function, batched=True)
    
    # 训练参数
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.lr,
        weight_decay=0.01,
        warmup_ratio=0.1,
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        fp16=True,
        gradient_accumulation_steps=4,
    )
    
    # 数据 collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False
    )
    
    # 创建 Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
    )
    
    print("开始训练...")
    trainer.train()
    
    # 保存模型
    print(f"保存模型到 {args.output_dir}...")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    
    # 如果需要合并模型
    if args.merge_model:
        print("\n开始合并 LoRA 权重到基础模型...")
        try:
            from peft import PeftModel
            
            # 加载基础模型
            print(f"加载基础模型：{args.base_model}...")
            base_model = AutoModelForCausalLM.from_pretrained(args.base_model, trust_remote_code=True)
            
            # 加载 LoRA adapter
            print("加载 LoRA adapter...")
            lora_model = PeftModel.from_pretrained(base_model, args.output_dir)
            
            # 合并权重
            print("合并权重中（这可能需要 2-3 分钟）...")
            merged_model = lora_model.merge_and_unload()
            
            # 保存合并后的模型
            merged_dir = f"{args.output_dir}_merged"
            print(f"保存合并后的模型到 {merged_dir}...")
            merged_model.save_pretrained(merged_dir, safe_serialization=True)
            tokenizer.save_pretrained(merged_dir)
            
            # 显示文件大小
            import os
            safetensors_file = os.path.join(merged_dir, "model.safetensors")
            if os.path.exists(safetensors_file):
                file_size_gb = os.path.getsize(safetensors_file) / (1024**3)
                print(f"[OK] 合并完成！生成文件：model.safetensors ({file_size_gb:.2f} GB)")
            else:
                # 可能是分片文件
                import glob
                files = glob.glob(os.path.join(merged_dir, "*.safetensors"))
                total_size = sum(os.path.getsize(f) for f in files)
                print(f"[OK] 合并完成！生成 {len(files)} 个文件，总计 {total_size/(1024**3):.2f} GB)")
            
        except Exception as e:
            print(f"[WARNING] 合并模型失败：{str(e)}")
            print("已保存 LoRA adapter，可以稍后手动合并")
    
    print("\n训练完成！")
    
    # 清理临时数据文件
    if args.data_dir.endswith('_temp'):
        print("\n开始清理临时数据文件...")
        try:
            import shutil
            if os.path.exists(args.data_dir):
                shutil.rmtree(args.data_dir)
                print(f"[OK] 已删除临时数据目录：{args.data_dir}")
        except Exception as e:
            print(f"[WARNING] 清理临时文件失败：{str(e)}")
    
    # 更新任务状态为完成
    if args.task_id:
        try:
            import json
            import os
            from datetime import datetime
            
            # 找到 tasks.json 文件
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            tasks_file = os.path.join(base_dir, 'storage', 'tasks.json')
            
            if os.path.exists(tasks_file):
                # 读取任务数据
                with open(tasks_file, 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
                
                # 更新任务状态
                for task in tasks:
                    if task.get('_id') == args.task_id:
                        task['status'] = 'completed'
                        task['progress'] = 100
                        task['updated_at'] = datetime.now().isoformat()
                        # 设置合并模型标志
                        task['merge_model'] = args.merge_model
                        print(f"[OK] 任务状态已更新为 completed")
                        break
                
                # 保存回文件
                with open(tasks_file, 'w', encoding='utf-8') as f:
                    json.dump(tasks, f, ensure_ascii=False, indent=2)
                    
        except Exception as e:
            print(f"[WARNING] 更新任务状态失败：{str(e)}")

if __name__ == "__main__":
    main()
