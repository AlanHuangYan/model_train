#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Merge LoRA adapter into base model
"""
import argparse
import os
import sys
import json

def main():
    parser = argparse.ArgumentParser(description='Merge LoRA weights into base model')
    parser.add_argument('--base_model', type=str, required=True, help='Base model path')
    parser.add_argument('--adapter_path', type=str, required=True, help='LoRA adapter path')
    parser.add_argument('--output_dir', type=str, required=True, help='Output directory')
    
    args = parser.parse_args()
    
    try:
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
        
        # 检查基础模型类型
        config_path = os.path.join(args.base_model, 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        is_multimodal = 'vision_config' in config_dict or 'image_token_id' in config_dict
        
        print(f"Loading base model: {args.base_model}...")
        print(f"模型类型：{'多模态' if is_multimodal else '纯文本'}")
        
        if is_multimodal:
            print("\n[警告] 检测到多模态模型 (Qwen3.5-VL)")
            print("由于以下原因，将只加载文本部分进行合并:")
            print("  1. LoRA 训练只涉及文本部分")
            print("  2. 视觉编码器未参与训练，无需合并")
            print("  3. 合并后的模型将只包含文本部分 (~1.4GB)，不包含视觉编码器")
            print("\n如需保留视觉模块，请手动使用 AutoModel 加载并合并")
            print("参考：https://github.com/huggingface/peft/issues/1168\n")
        
        print(f"加载基础模型...")
        base_model = AutoModelForCausalLM.from_pretrained(
            args.base_model,
            trust_remote_code=True
        )
        
        print(f"加载 LoRA adapter: {args.adapter_path}...")
        lora_model = PeftModel.from_pretrained(base_model, args.adapter_path)
        
        print("合并权重中（这可能需要 2-3 分钟）...")
        merged_model = lora_model.merge_and_unload()
        
        print(f"保存合并后的模型到 {args.output_dir}...")
        merged_model.save_pretrained(args.output_dir, safe_serialization=True)
        
        # Save tokenizer
        tokenizer_path = os.path.join(args.adapter_path, 'tokenizer.json')
        if os.path.exists(tokenizer_path):
            tokenizer = AutoTokenizer.from_pretrained(args.adapter_path)
            tokenizer.save_pretrained(args.output_dir)
        else:
            tokenizer = AutoTokenizer.from_pretrained(args.base_model)
            tokenizer.save_pretrained(args.output_dir)
        
        # Show file size
        safetensors_file = os.path.join(args.output_dir, "model.safetensors")
        if os.path.exists(safetensors_file):
            file_size_gb = os.path.getsize(safetensors_file) / (1024**3)
            print(f"[OK] 合并完成！生成文件：model.safetensors ({file_size_gb:.2f} GB)")
        else:
            # May be sharded files
            import glob
            files = glob.glob(os.path.join(args.output_dir, "*.safetensors"))
            total_size = sum(os.path.getsize(f) for f in files)
            print(f"[OK] 合并完成！生成 {len(files)} 个文件，总计 {total_size/(1024**3):.2f} GB")
        
        if is_multimodal:
            print("\n[注意] 合并后的模型是纯文本模型，不包含视觉编码器")
            print("如果需要视觉能力，请使用基础模型 + LoRA adapter 的方式使用")
        
        print("\n合并后的模型可以独立使用，不需要基础模型!")
        
    except Exception as e:
        print(f"[ERROR] 合并失败：{str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
