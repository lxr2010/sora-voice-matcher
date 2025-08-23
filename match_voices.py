import json
import os
import re
import argparse
import logging
from sentence_transformers import SentenceTransformer, util
import torch
import wave
import struct
from pathlib import Path


def create_empty_wav_file(path):
    """在指定路径创建一个统一的、短小的静音WAV文件。"""
    sample_rate = 22050  # VITS default sample rate
    duration_ms = 100
    channels = 1
    sampwidth = 2  # 16-bit
    num_frames = int(duration_ms * (sample_rate / 1000.0))

    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sampwidth)
        wav_file.setframerate(sample_rate)
        frame = struct.pack('<h', 0)
        wav_file.writeframes(frame * num_frames)

# --- 配置 ---
# 新版本（重制版）语音数据文件
NEW_VOICE_FILE = r'KuroTools v1.3\scripts&tables\t_voice.json'
# 旧版本语音数据文件
OLD_VOICE_FILE = 'voice_data.json'
# 输出文件：成功匹配的数据
MERGED_OUTPUT_FILE = 'merged_voice_data.json'
# 输出文件：未成功匹配的数据
UNMATCHED_OUTPUT_FILE = 'unmatched_voice_data.json'


def normalize_text(text):
    """移除文本中的所有标点符号和空格，用于匹配。"""
    # 此正则表达式应能处理日文和英文标点
    return re.sub(r'[\s\W]', '', text)

def classify_voice_file(filename):
    """
    根据文件名对语音文件进行分类。

    Args:
        filename (str): 语音文件的名称。

    Returns:
        dict: 包含分类信息的字典。
              例如 {'type': 'character_voice', 'character_id': '001', 'category': 'main', 'number': '0001'}
              或 {'type': 'sound_effect', 'description': 'cat_02'}
    """
    # 角色语音: v<角色ID>_<类型>_<序号>.wav (e.g., v001_00_0001.wav, v327_gs_0002.wav)
    match = re.match(r'^v(\d{3})_(\w{2})_(\d{4})\.wav$', filename)
    if match:
        char_id, category_code, number = match.groups()
        category_map = {
            '00': 'main',
            'av': 'event',
            'bv': 'battle_extra',
            'gs': 'scene_gs',
            'gy': 'scene_gy'
        }
        return {
            'type': 'character_voice',
            'character_id': char_id,
            'category': category_map.get(category_code, 'unknown'),
            'number': number
        }

    # 战斗/系统语音: v<角色ID>_<类型><序号>.wav (e.g., v001_b0001.wav, v001_s0001.wav, v001_b0118b.wav)
    match = re.match(r'^v(\d{3})_([bs])(\d{4}[b]?)\.wav$', filename)
    if match:
        char_id, category_code, number = match.groups()
        category_map = {
            'b': 'battle',
            's': 'system'
        }
        return {
            'type': 'character_voice',
            'character_id': char_id,
            'category': category_map.get(category_code, 'unknown'),
            'number': number
        }

    # 音效: v_se_<描述>.wav (e.g., v_se_cat_02.wav)
    match = re.match(r'^v_se_(.*)\.wav$', filename)
    if match:
        description = match.group(1)
        return {
            'type': 'sound_effect',
            'description': description
        }

    return {'type': 'unknown', 'filename': filename}

def find_best_match(new_entry, old_data_map, old_data_normalized_map, old_data_list, model, old_embeddings, args):
    """执行三步匹配策略来查找最佳匹配。"""
    new_text = new_entry['text']

    # 1. 精确匹配
    if new_text in old_data_map:
        return old_data_map[new_text], 'exact'

    # 2. 移除标点后匹配
    normalized_new_text = normalize_text(new_text)
    if normalized_new_text and normalized_new_text in old_data_normalized_map:
        return old_data_normalized_map[normalized_new_text], 'normalized'

    # 3. 如果精确匹配和标准化匹配都失败，并且未禁用相似度搜索，则使用向量相似度进行最终匹配
    if not args.no_similarity_search:
        query_embedding = model.encode(new_text, convert_to_tensor=True)
        hits = util.semantic_search(query_embedding, old_embeddings, top_k=1)
        if hits and hits[0][0]['score'] > args.similarity_threshold:
            best_match = old_data_list[hits[0][0]['corpus_id']]
            score = hits[0][0]['score']
            match_type = f'vector_search ({score:.2f})'
            return best_match, match_type

    return None, None

def create_silent_wav(path, duration_ms=100):
    """
    Creates a silent WAV file.

    :param path: Path to save the WAV file.
    :param duration_ms: Duration of the silence in milliseconds.
    """
    sample_rate = 22050  # VITS default sample rate
    channels = 1
    sampwidth = 2  # 16-bit
    num_frames = int(duration_ms * (sample_rate / 1000.0))

    with wave.open(str(path), 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sampwidth)
        wav_file.setframerate(sample_rate)
        # Write zero frames for silence
        frame = struct.pack('<h', 0)
        wav_file.writeframes(frame * num_frames)

def main():
    """主函数，执行匹配和生成文件。"""
    parser = argparse.ArgumentParser(description='匹配新旧语音数据。')
    parser.add_argument(
        '--character-ids',
        nargs='+',
        help='只匹配指定的角色ID（可提供多个，以空格分隔）。'
    )
    parser.add_argument(
        '--match-battle-only',
        action='store_true',
        help='只匹配战斗语音（默认不处理）。'
    )
    parser.add_argument(
        '--match-battle',
        action='store_true',
        help='匹配战斗语音（默认不处理）。'
    )
    parser.add_argument(
        '--match-sfx',
        action='store_true',
        help='包括音效文件（默认不处理）。'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='输出详细的日志信息，包括跳过的条目。'
    )
    parser.add_argument('--no-similarity-search', action='store_true', help='禁用向量相似度搜索')
    parser.add_argument('--similarity-threshold', type=float, default=0.85, help='设置向量相似度搜索的阈值 (默认: 0.85)')
    parser.add_argument('--no-map-failed-to-empty', dest='map_failed_to_empty', action='store_false', help='禁用“将匹配失败的语音指向空WAV文件”的功能（默认开启）。')
    args = parser.parse_args()

    # 根据 --verbose 参数配置日志记录
    if args.verbose:
        logging.basicConfig(level=logging.INFO, format='%(message)s')
    else:
        logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

    # 如果启用了映射到空文件功能，则提前创建该文件
    if args.map_failed_to_empty:
        empty_wav_path = Path('voice/wav/EMPTY.wav')
        create_empty_wav_file(empty_wav_path)
        logging.info(f"已创建或更新统一的空WAV文件: {empty_wav_path}")

    try:
        with open(NEW_VOICE_FILE, 'r', encoding='utf-8') as f:
            new_data = json.load(f)['data'][0]['data']
        with open(OLD_VOICE_FILE, 'r', encoding='utf-8') as f:
            old_data_list = json.load(f)
    except FileNotFoundError as e:
        print(f"错误：找不到文件 {e.filename}")
        return
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"错误：解析JSON文件或找不到键时出错: {e}")
        return

    # 加载预训练的 sentence-transformer 模型
    # 'paraphrase-multilingual-MiniLM-L12-v2' 是一个性能优秀的多语言模型
    print("正在加载文本向量化模型...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    print("模型加载完成。")

    # 为旧数据创建向量嵌入
    print("正在为旧语音数据创建向量嵌入...")
    old_texts = [entry.get('text', '') for entry in old_data_list]
    old_embeddings = model.encode(old_texts, convert_to_tensor=True)
    print("向量嵌入创建完成。")

    # 为旧数据创建快速查找映射
    old_data_map = {entry['text']: entry for entry in old_data_list if entry.get('text')}
    old_data_normalized_map = {normalize_text(entry['text']): entry for entry in old_data_list if entry.get('text')}

    matched_data = []
    unmatched_data = []
    
    total_count = len(new_data)
    success_count = 0
    processed_count = 0
    vector_search_success_count = 0

    print(f"开始处理 {total_count} 条重制版语音数据...")

    for new_entry in new_data:
        # 必须有文本和文件名才能继续
        if 'text' not in new_entry or not new_entry['text'] or 'filename' not in new_entry:
            continue

        # 对每个条目进行分类
        classification = classify_voice_file(f"{new_entry['filename']}.wav")

        # 根据命令行参数决定是否处理此条目
        should_process = False
        reason = "未知类型"
        is_battle = classification.get('category') == 'battle'
        is_sfx = classification['type'] == 'sound_effect'
        is_character_voice = classification['type'] == 'character_voice'

        any_filter_provided = any([
            args.match_battle,
            args.match_sfx,
            args.match_battle_only,
            args.character_ids
        ])

        if not any_filter_provided:
            if is_character_voice:
                should_process = True
            else:
                reason = "非角色语音（默认模式）"
        elif args.match_battle_only:
            if is_battle:
                should_process = True
            else:
                reason = "非战斗语音（--match-battle-only 模式）"
        else:
            # 默认处理非战斗角色语音
            if is_character_voice and not is_battle:
                should_process = True
            # 如果 --match-battle 开启，额外处理战斗语音
            if is_battle and args.match_battle:
                should_process = True
            # 如果 --match-sfx 开启，额外处理音效
            if is_sfx and args.match_sfx:
                should_process = True
            
            # 如果不满足任何处理条件，确定跳过原因
            if not should_process:
                if is_battle:
                    reason = "战斗语音（默认跳过）"
                elif is_sfx:
                    reason = "音效（默认跳过）"
                else:
                    reason = "不满足任何匹配条件"

        if not should_process:
            logging.info(f"跳过 {new_entry['filename']}: {reason}")
            continue

        # 角色ID过滤（适用于所有通过上述检查的条目）
        if args.character_ids and classification.get('character_id') not in args.character_ids:
            logging.info(f"跳过 {new_entry['filename']}: 角色ID不匹配 (需要 {args.character_ids}, 实际是 {classification.get('character_id')})")
            continue

        processed_count += 1
        best_match, match_type = find_best_match(new_entry, old_data_map, old_data_normalized_map, old_data_list, model, old_embeddings, args)

        if best_match:
            success_count += 1
            if match_type.startswith('vector_search'):
                vector_search_success_count += 1
            
            # 从 new_entry 获取文件名并进行分类
            new_filename = new_entry.get('filename')
            classification = classify_voice_file(f"{new_filename}.wav") if new_filename else {'type': 'unknown'}

            merged_entry = {
                'new_voice_id': new_entry.get('id'),
                'new_filename': new_filename,
                'new_text': new_entry['text'],
                'old_voice_id': best_match.get('voice_id'),
                'old_text': best_match.get('text'),
                'character_id': best_match.get('character_id'),
                'source_file': best_match.get('source_file'),
                'match_type': match_type,
                'classification': classification
            }
            matched_data.append(merged_entry)
        else:
            unmatched_data.append({
                'new_voice_id': new_entry.get('id'),
                'text': new_entry['text']
            })

    # 写入输出文件
    with open(MERGED_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(matched_data, f, ensure_ascii=False, indent=4)
    
    with open(UNMATCHED_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(unmatched_data, f, ensure_ascii=False, indent=4)

    # --- 更新 t_voice.json ---
    print("\n正在将匹配结果应用到新的 t_voice.json...")
    
    # 1. 创建已匹配和未匹配的ID查找集
    id_to_old_filename_map = {entry['new_voice_id']: "ch" + entry['old_voice_id'][:-1] for entry in matched_data}
    unmatched_ids = {entry['new_voice_id'] for entry in unmatched_data}

    # 2. 重新加载原始 t_voice.json 数据
    try:
        with open(NEW_VOICE_FILE, 'r', encoding='utf-8') as f:
            t_voice_content = json.load(f)
        
        # 假设数据结构总是 'data' -> list -> 'data' -> list of entries
        voice_entries = t_voice_content['data'][0]['data']

        # 3. 遍历并更新 t_voice.json 数据
        updated_count = 0
        unmatched_mapped_count = 0
        for entry in voice_entries:
            voice_id = entry.get('id')
            if voice_id in id_to_old_filename_map:
                entry['filename'] = id_to_old_filename_map[voice_id]
                updated_count += 1
            elif args.map_failed_to_empty and voice_id in unmatched_ids:
                entry['filename'] = 'EMPTY'
                unmatched_mapped_count += 1

        print(f"\n成功更新 {updated_count} 个已匹配的语音条目。")
        if args.map_failed_to_empty:
            print(f"已将 {unmatched_mapped_count} 个未匹配的语音条目指向 EMPTY.wav。")

        # 4. 确保 output 目录存在
        output_dir = 'output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 5. 写入新的 t_voice.json 文件
        output_t_voice_path = os.path.join(output_dir, 't_voice.json')
        with open(output_t_voice_path, 'w', encoding='utf-8') as f:
            json.dump(t_voice_content, f, ensure_ascii=False, indent=4)
        
        print(f"成功更新 {updated_count} 个条目。")
        print(f"新的 t_voice.json 已保存到: {output_t_voice_path}")

    except Exception as e:
        print(f"错误：更新 t_voice.json 失败: {e}")

    # --- 打印统计结果 ---
    print("\n--- 匹配完成 ---")
    print(f"总计 (输入文件): {total_count}")
    print(f"处理 (符合条件): {processed_count}")
    print(f"成功: {success_count} (其中向量搜索: {vector_search_success_count})")
    print(f"失败: {processed_count - success_count}")
    print(f"成功匹配的数据已保存到: {MERGED_OUTPUT_FILE}")
    print(f"未匹配的数据已保存到: {UNMATCHED_OUTPUT_FILE}")

if __name__ == '__main__':
    main()
