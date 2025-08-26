import json

# --- 配置 ---
MERGED_FILE = 'merged_voice_data.json'
UNMATCHED_FILE = 'unmatched_voice_data.json'
OLD_VOICE_FILE = 'voice_data.json'
OUTPUT_FILE = 'context_analysis_report.json'

def parse_voice_id(voice_id):
    """从语音ID（如 '0940010128V'）中提取数字部分。"""
    try:
        # 移除末尾的 'V' 并转换为整数
        return int(voice_id[3:-1])
    except (ValueError, TypeError):
        return None

def find_old_entry_by_numeric_id(numeric_id, old_voice_map):
    """通过数字ID查找原始语音条目。"""
    # 重新构建可能的ID格式，例如补零
    # 注意：这里的格式可能需要根据实际情况调整
    possible_id = f"{numeric_id:010d}V"
    return old_voice_map.get(possible_id)

def main():
    """主函数，执行上下文分析。"""
    try:
        with open(MERGED_FILE, 'r', encoding='utf-8') as f:
            merged_data = json.load(f)
        with open(UNMATCHED_FILE, 'r', encoding='utf-8') as f:
            unmatched_data = json.load(f)
        with open(OLD_VOICE_FILE, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
    except FileNotFoundError as e:
        print(f"错误：找不到文件 {e.filename}")
        return

    # --- 数据准备 ---
    # 创建高效的查找映射
    merged_map = {entry['new_voice_id']: entry for entry in merged_data}
    unmatched_map = {entry['new_voice_id']: entry for entry in unmatched_data}
    old_voice_map = {entry['voice_id']: entry for entry in old_data}

    analysis_report = []
    processed_unmatched_ids = set()

    print(f"开始分析 {len(unmatched_data)} 条未匹配数据...")

    # 遍历所有未匹配的条目
    for unmatched_entry in sorted(unmatched_data, key=lambda x: x['new_voice_id']):
        unmatched_id = unmatched_entry['new_voice_id']

        if unmatched_id in processed_unmatched_ids:
            continue

        # 寻找上下文（前一条和后一条）
        prev_id = unmatched_id - 1
        next_id = unmatched_id + 1

        # 检查前后条目是否都在已匹配的数据中
        if prev_id in merged_map and next_id in merged_map:
            prev_match = merged_map[prev_id]
            next_match = merged_map[next_id]

            prev_old_id_num = parse_voice_id(prev_match.get('old_voice_id'))
            next_old_id_num = parse_voice_id(next_match.get('old_voice_id'))

            # 确认旧ID是连续的，中间只差一个
            if prev_old_id_num and next_old_id_num and (next_old_id_num - prev_old_id_num) == 2:
                inferred_old_id_num = prev_old_id_num + 1
                inferred_old_entry = find_old_entry_by_numeric_id(inferred_old_id_num, old_voice_map)

                if inferred_old_entry:
                    context = {
                        'unmatched_new_voice_id': unmatched_id,
                        'comparison': [
                            {
                                'context': 'previous',
                                'new_text': prev_match.get('new_text'),
                                'old_text': prev_match.get('old_text'),
                            },
                            {
                                'context': 'current_unmatched',
                                'new_text': unmatched_entry.get('text'),
                                'old_text': inferred_old_entry.get('text'),
                            },
                            {
                                'context': 'next',
                                'new_text': next_match.get('new_text'),
                                'old_text': next_match.get('old_text'),
                            }
                        ]
                    }
                    analysis_report.append(context)
                    processed_unmatched_ids.add(unmatched_id)

    # 保存报告
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(analysis_report, f, ensure_ascii=False, indent=4)

    print("\n--- 分析完成 ---")
    print(f"发现并报告了 {len(analysis_report)} 个有问题的上下文。")
    print(f"报告已保存到: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
