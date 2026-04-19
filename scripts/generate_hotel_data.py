#!/usr/bin/env python3
"""
生成酒店客服训练数据
目标：生成约 2000 条训练数据
"""

import json
import random
from pathlib import Path

# 定义酒店客服场景的对话模板
SCENARIOS = {
    "reservation": {
        "templates": [
            ("我想预订一间房间", "好的，请问您计划什么时候入住？需要住几晚呢？"),
            ("我要订房", "请问您需要什么类型的房间？我们有标准间、大床房和套房。"),
            ("帮我预订一个房间", "好的，请问入住日期和离店日期是什么时候？"),
            ("我想预约房间", "请问您几位入住？我们需要为您安排合适的房型。"),
            ("有空的房间吗", "有的，请问您想要什么类型的房间？我们还有标准间和大床房。"),
        ],
        "variations": [
            ("我想预订一间{room_type}房", "好的，请问您计划什么时候入住？需要住几晚呢？"),
            ("我要订一个{room_type}房间", "请问您需要什么日期入住？"),
            ("帮我预订{room_type}", "好的，请问入住日期和离店日期是什么时候？"),
        ],
        "room_types": ["标准", "大床", "豪华", "商务", "行政"],
    },
    
    "inquiry": {
        "templates": [
            ("酒店有健身房吗？", "是的，我们酒店配有 24 小时开放的健身房，位于 3 楼，住店客人可以免费使用。"),
            ("有游泳池吗？", "有的，我们的室内恒温游泳池位于 2 楼，开放时间是早上 6 点到晚上 10 点。"),
            ("酒店提供早餐吗？", "是的，我们提供自助早餐，供应时间是早上 6:30 到 10:00，在一楼餐厅。"),
            ("有停车场吗？", "有的，酒店提供免费停车场，住店客人可以直接使用。"),
            ("WiFi 怎么连接？", "酒店全覆盖免费 WiFi，房间名是 Hotel_Guest，密码是您的房间号。"),
            ("附近有什么景点吗？", "酒店附近有很多景点，步行 5 分钟有中央公园，10 分钟有购物中心。"),
            ("可以寄存行李吗？", "可以的，我们提供免费的行李寄存服务，退房后也可以寄存。"),
            ("有接送机服务吗？", "有的，我们提供机场接送服务，需要提前 24 小时预约，费用是 200 元。"),
        ],
        "variations": [],
    },
    
    "check_in_out": {
        "templates": [
            ("我想办理入住", "好的，请提供您的预订信息和身份证件。"),
            ("我要退房", "好的，请问您需要开具发票吗？"),
            ("入住时间是什么时候？", "我们的标准入住时间是下午 2 点后，退房时间是中午 12 点前。"),
            ("可以延迟退房吗？", "可以的，延迟退房会根据房型收取一定费用，具体可以咨询前台。"),
            ("几点可以入住？", "入住时间是下午 2 点后，如果您提前到达，我们可以先帮您寄存行李。"),
        ],
        "variations": [],
    },
    
    "complaint": {
        "templates": [
            ("房间太吵了", "非常抱歉给您带来不便，我马上为您查看是否可以换到安静的房间。"),
            ("空调坏了", "很抱歉，我马上安排工程部人员去您房间检修，请稍等。"),
            ("房间不干净", "非常抱歉，我们会立即安排客房服务人员重新打扫您的房间。"),
            ("WiFi 连不上", "很抱歉给您带来不便，我让技术人员去帮您检查一下。"),
            ("隔壁太吵了", "非常抱歉，我马上联系隔壁客人提醒他们保持安静。"),
        ],
        "variations": [],
    },
    
    "service": {
        "templates": [
            ("可以送些毛巾来吗？", "好的，马上为您安排客房服务送毛巾到您房间。"),
            ("我要叫客房服务", "好的，请问您需要什么服务？打扫房间还是其他服务？"),
            ("需要多两瓶水", "好的，我让客房服务给您送两瓶水过去。"),
            ("可以帮忙叫出租车吗？", "可以的，请问您什么时候需要用车？我帮您安排。"),
            ("餐厅在哪里？", "我们酒店的餐厅在一楼，早餐时间是 6:30-10:00，午餐 11:30-14:00，晚餐 17:30-21:00。"),
        ],
        "variations": [],
    },
}

def generate_reservation_data():
    """生成预订相关数据"""
    data = []
    scenario = SCENARIOS["reservation"]
    
    # 添加固定模板
    for question, answer in scenario["templates"]:
        data.append({
            "instruction": question,
            "input": "",
            "output": answer
        })
    
    # 生成变体数据
    for template_q, template_a in scenario["variations"]:
        for room_type in scenario["room_types"]:
            question = template_q.format(room_type=room_type)
            data.append({
                "instruction": question,
                "input": "",
                "output": template_a
            })
    
    return data

def generate_inquiry_data():
    """生成咨询相关数据"""
    data = []
    scenario = SCENARIOS["inquiry"]
    
    for question, answer in scenario["templates"]:
        data.append({
            "instruction": question,
            "input": "",
            "output": answer
        })
    
    return data

def generate_checkin_data():
    """生成入住退房相关数据"""
    data = []
    scenario = SCENARIOS["check_in_out"]
    
    for question, answer in scenario["templates"]:
        data.append({
            "instruction": question,
            "input": "",
            "output": answer
        })
    
    return data

def generate_complaint_data():
    """生成投诉处理相关数据"""
    data = []
    scenario = SCENARIOS["complaint"]
    
    for question, answer in scenario["templates"]:
        data.append({
            "instruction": question,
            "input": "",
            "output": answer
        })
    
    return data

def generate_service_data():
    """生成服务请求相关数据"""
    data = []
    scenario = SCENARIOS["service"]
    
    for question, answer in scenario["templates"]:
        data.append({
            "instruction": question,
            "input": "",
            "output": answer
        })
    
    return data

def expand_data_with_variations(base_data, target_count=2000):
    """通过添加细微变化来扩展数据集"""
    expanded = base_data.copy()
    
    # 同义词替换
    synonyms = {
        "预订": ["预约", "订购", "预定"],
        "房间": ["客房", "屋子"],
        "酒店": ["宾馆", "旅店"],
        "入住": ["住店", "入住酒店"],
        "退房": ["结账", "离店"],
    }
    
    while len(expanded) < target_count:
        # 随机选择一个基础数据
        base = random.choice(base_data)
        instruction = base["instruction"]
        output = base["output"]
        
        # 随机应用同义词替换
        for word, syns in synonyms.items():
            if word in instruction and random.random() > 0.5:
                new_word = random.choice(syns)
                instruction = instruction.replace(word, new_word, 1)
                break
        
        # 添加轻微变化的回答
        output_variations = [
            output,
            output + " 请问还有什么可以帮助您的？",
            "好的，" + output if not output.startswith("好的") else output,
        ]
        
        expanded.append({
            "instruction": instruction,
            "input": "",
            "output": random.choice(output_variations)
        })
    
    return expanded[:target_count]

def save_jsonl(data, filepath):
    """保存为 JSONL 格式"""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"已保存 {len(data)} 条数据到 {filepath}")

def main():
    """主函数"""
    print("开始生成酒店客服训练数据...")
    
    # 生成各类数据
    reservation_data = generate_reservation_data()
    print(f"预订相关数据：{len(reservation_data)} 条")
    
    inquiry_data = generate_inquiry_data()
    print(f"咨询相关数据：{len(inquiry_data)} 条")
    
    checkin_data = generate_checkin_data()
    print(f"入住退房数据：{len(checkin_data)} 条")
    
    complaint_data = generate_complaint_data()
    print(f"投诉处理数据：{len(complaint_data)} 条")
    
    service_data = generate_service_data()
    print(f"服务请求数据：{len(service_data)} 条")
    
    # 合并所有数据
    all_data = reservation_data + inquiry_data + checkin_data + complaint_data + service_data
    print(f"\n基础数据总数：{len(all_data)} 条")
    
    # 扩展到目标数量
    expanded_data = expand_data_with_variations(all_data, target_count=2200)
    print(f"扩展后数据总数：{len(expanded_data)} 条")
    
    # 随机打乱
    random.shuffle(expanded_data)
    
    # 划分训练集、验证集、测试集 (80/10/10)
    train_size = int(len(expanded_data) * 0.8)
    val_size = int(len(expanded_data) * 0.1)
    
    train_data = expanded_data[:train_size]
    val_data = expanded_data[train_size:train_size + val_size]
    test_data = expanded_data[train_size + val_size:]
    
    # 保存
    data_dir = Path("data/hotel_customer_service")
    save_jsonl(train_data, data_dir / "train.jsonl")
    save_jsonl(val_data, data_dir / "val.jsonl")
    save_jsonl(test_data, data_dir / "test.jsonl")
    
    print(f"\n数据分布：")
    print(f"  训练集：{len(train_data)} 条")
    print(f"  验证集：{len(val_data)} 条")
    print(f"  测试集：{len(test_data)} 条")

if __name__ == "__main__":
    main()
