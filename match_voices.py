import json
import os
import re
import argparse
import logging
from collections import defaultdict
from sentence_transformers import SentenceTransformer, util
import torch
import wave
import struct
from pathlib import Path
import sys
import io

# --- Logging Setup ---
# Create logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG) # Set lowest level to capture all messages

# Create file handler which logs even debug messages
fh = logging.FileHandler('match_voice.log', mode='w', encoding='utf-8')
fh.setLevel(logging.DEBUG)

# Create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Create formatter and add it to the handlers
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_formatter = logging.Formatter('%(message)s')
fh.setFormatter(file_formatter)
ch.setFormatter(console_formatter)

# Add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


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
# 旧版本脚本数据文件
OLD_SCRIPT_FILE = 'script_data.json'
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
    match = re.match(r'^v(\d{3})_(\w{2})_(\d{4}[br]?)\.wav$', filename)
    if match:
        char_id, category_code, number = match.groups()

        category = 'unknown'
        if category_code.isdigit():
            category = 'main'
        else:
            category_map = {
                'av': 'active_voice',
                'bv': 'battle_voice'
            }
            category = category_map.get(category_code, 'unknown')

        return {
            'type': 'character_voice',
            'character_id': char_id,
            'category': category,
            'number': number
        }

    # 战斗/系统语音: v<角色ID>_<类型><序号>.wav (e.g., v001_b0001.wav, v001_s0001.wav, v001_b0118b.wav)
    match = re.match(r'^v(\d{3})_([bs])(\d{4}[br]?)\.wav$', filename)
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

def find_best_match(new_entry, old_data_map, old_data_normalized_map, old_script_list, model, old_embeddings, args, used_old_voice_ids, methods):
    """执行指定方法的匹配策略来查找最佳匹配。"""
    new_text = new_entry['text']

    # 1. 精确匹配
    if 'exact' in methods and new_text in old_data_map:
        for candidate in old_data_map[new_text]:
            if candidate['voice_id'] not in used_old_voice_ids:
                return candidate, 'exact'

    # 2. 移除标点后匹配
    if 'normalized' in methods and (normalized_new_text := normalize_text(new_text)) and normalized_new_text in old_data_normalized_map:
        for candidate in old_data_normalized_map[normalized_new_text]:
            if candidate['voice_id'] not in used_old_voice_ids:
                return candidate, 'normalized'

    # 3. 向量相似度匹配
    if 'vector' in methods and not args.no_similarity_search:
        contextual_new_text = f"{new_entry.get('context_prev', '')} {new_text} {new_entry.get('context_next', '')}".strip()
        query_embedding = model.encode(contextual_new_text, convert_to_tensor=True)
        hits = util.semantic_search(query_embedding, old_embeddings, top_k=1)
        if hits and hits[0][0]['score'] > args.similarity_threshold:
            best_match_candidate = old_script_list[hits[0][0]['corpus_id']]
            score = hits[0][0]['score']
            match_type = f'vector_search ({score:.2f})'
            return best_match_candidate, match_type

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
        '--match-active',
        action='store_true',
        help='匹配主动语音 (av category)。默认不匹配。'
    )
    parser.add_argument(
        '--match-battle',
        action='store_true',
        help='匹配战斗语音 (b, bv category)。默认不匹配。'
    )
    parser.add_argument(
        '--match-other',
        action='store_true',
        help='匹配分类为 unknown 的语音。默认不匹配。'
    )
    parser.add_argument(
        '--match-sfx',
        action='store_true',
        help='匹配音效文件 (v_se_*)。默认不匹配。'
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

    # 如果启用了映射到空文件功能，则提前创建该文件
    if args.map_failed_to_empty:
        empty_wav_path = Path('voice/wav/EMPTY.wav')
        create_empty_wav_file(empty_wav_path)
        logger.info(f"已创建或更新统一的空WAV文件: {empty_wav_path}")

    try:
        with open(NEW_VOICE_FILE, 'r', encoding='utf-8') as f:
            new_data = json.load(f)['data'][0]['data']
        with open(OLD_VOICE_FILE, 'r', encoding='utf-8') as f:
            old_data_list = json.load(f)
        with open(OLD_SCRIPT_FILE, 'r', encoding='utf-8') as f:
            old_script_list = json.load(f)
    except FileNotFoundError as e:
        logger.error(f"错误：找不到文件 {e.filename}")
        return
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.error(f"错误：解析JSON文件或找不到键时出错: {e}")
        return

    # 为新语音数据添加上下文
    logger.info("正在为新语音数据添加上下文...")
    # 根据 'id' 字段排序以确保对话顺序
    new_data.sort(key=lambda x: x.get('id', ''))
    for i, entry in enumerate(new_data):
        # 添加上一句上下文
        if i > 0:
            entry['context_prev'] = new_data[i-1].get('text', '')
        else:
            entry['context_prev'] = ""
            
        # 添加下一句上下文
        if i < len(new_data) - 1:
            entry['context_next'] = new_data[i+1].get('text', '')
        else:
            entry['context_next'] = ""
    logger.info("上下文添加完成。")

    # 为旧语音数据添加上下文
    logger.info("正在为旧语音数据添加上下文...")
    # 从 voice_id 解析场景信息并排序
    for entry in old_data_list:
        voice_id = entry.get('voice_id', '')
        if isinstance(voice_id, str) and len(voice_id) >= 10:
            entry['scene_id'] = voice_id[3:6]
            entry['scene_seq_id'] = int(voice_id[6:10])
        else:
            # 为不符合格式的ID设置默认值以便排序
            entry['scene_id'] = ""
            entry['scene_seq_id'] = -1

    old_data_list.sort(key=lambda x: (x.get('scene_id', ''), x.get('scene_seq_id', '')))
    for i, entry in enumerate(old_data_list):
        # 检查是否在同一场景内
        is_same_scene_prev = (i > 0 and 
                              old_data_list[i-1].get('scene_id') == entry.get('scene_id'))
        
        is_same_scene_next = (i < len(old_data_list) - 1 and 
                              old_data_list[i+1].get('scene_id') == entry.get('scene_id'))

        # 添加上一句上下文
        if is_same_scene_prev:
            entry['context_prev'] = old_data_list[i-1].get('text', '')
        else:
            entry['context_prev'] = ""
        
        # 添加下一句上下文
        if is_same_scene_next:
            entry['context_next'] = old_data_list[i+1].get('text', '')
        else:
            entry['context_next'] = ""
    logger.info("旧数据上下文添加完成。")

    if not args.no_similarity_search:
        # 加载预训练的 sentence-transformer 模型
        # 'paraphrase-multilingual-MiniLM-L12-v2' 是一个性能优秀的多语言模型
        logger.info("正在加载文本向量化模型...")
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        logger.info("模型加载完成。")

        # 为旧数据创建向量嵌入
        logger.info("正在为旧脚本数据创建上下文向量嵌入...")
        old_contextual_texts = [
            f"{entry.get('context_prev', '')} {entry.get('text', '')} {entry.get('context_next', '')}".strip()
            for entry in old_script_list
        ]
        old_embeddings = model.encode(old_contextual_texts, convert_to_tensor=True)
        logger.info("向量嵌入创建完成。")
    else:
        logger.info("跳过向量嵌入创建，因为 --no-similarity-search 被设置。")
        model = None
        old_embeddings = None

    # 为旧数据创建快速查找映射（一个文本可能对应多个语音）
    old_data_map = defaultdict(list)
    old_data_normalized_map = defaultdict(list)
    for entry in old_data_list:
        if text := entry.get('text'):
            # 精确匹配映射
            old_data_map[text].append(entry)
            
            # 标准化文本映射
            normalized_text = normalize_text(text)
            if normalized_text:
                old_data_normalized_map[normalized_text].append(entry)

    # 为旧脚本数据创建快速查找映射
    old_script_map = defaultdict(list)
    for entry in old_script_list:
        if text := entry.get('text'):
            old_script_map[text].append(entry)

    # 创建 voice_id 到 old_data_list 条目的映射
    old_voice_id_to_entry_map = {e['voice_id']: e for e in old_data_list}

    # 对候选项列表进行排序，确保优先匹配文件名靠前的语音
    logger.info("正在对具有相同文本的候选项进行排序...")
    for text in old_data_map:
        old_data_map[text].sort(key=lambda e: e.get('voice_id', ''))
    for text in old_data_normalized_map:
        old_data_normalized_map[text].sort(key=lambda e: e.get('voice_id', ''))
    for text in old_script_map:
        old_script_map[text].sort(key=lambda e: e.get('script_id', 0))
    logger.info("排序完成。")

    matched_data = []
    unmatched_data = []
    used_old_voice_ids = set() # 用于跟踪已匹配的旧语音ID
    
    total_count = len(new_data)
    processed_count = 0
    vector_search_success_count = 0

    # 筛选出需要处理的条目
    entries_to_process = []
    for new_entry in new_data:
        if 'text' not in new_entry or not new_entry['text'] or 'filename' not in new_entry:
            continue

        classification = classify_voice_file(f"{new_entry['filename']}.wav")
        category = classification.get('category')
        file_type = classification.get('type')

        allowed_categories = {'main'}
        if args.match_active: allowed_categories.add('active_voice')
        if args.match_battle: allowed_categories.add('battle'); allowed_categories.add('battle_voice')
        if args.match_other: allowed_categories.add('unknown')

        should_process = False
        if file_type == 'sound_effect' and args.match_sfx:
            should_process = True
        elif file_type == 'character_voice' and category in allowed_categories:
            should_process = True

        if args.character_ids and classification.get('character_id') not in args.character_ids:
            should_process = False

        if should_process:
            entries_to_process.append(new_entry)
        else:
            reason = f"类别 '{category or file_type}' 未被命令行选项启用或角色ID不匹配"
            logger.info(f"跳过 {new_entry['filename']}: {reason}")

    processed_count = len(entries_to_process)
    logger.info(f"开始处理 {processed_count} 条符合条件的语音数据...")

    # --- Pass 1: Exact and Normalized Matching ---
    logger.info("\n--- 第一遍: 执行精确匹配和标准化匹配 ---")
    remaining_entries_pass2 = []
    pass1_success_count = 0
    for new_entry in entries_to_process:
        best_match, match_type = find_best_match(new_entry, old_data_map, old_data_normalized_map, old_script_list, model, old_embeddings, args, used_old_voice_ids, methods=['exact', 'normalized'])

        if best_match:
            pass1_success_count += 1
            used_old_voice_ids.add(best_match['voice_id'])
            classification = classify_voice_file(f"{new_entry.get('filename')}.wav")
            matched_data.append({
                'new_voice_id': new_entry.get('id'),
                'new_filename': new_entry.get('filename'),
                'new_text': new_entry['text'],
                'old_voice_id': best_match.get('voice_id'),
                'old_scene_id': best_match.get('scene_id'),
                'old_scene_seq_id': best_match.get('scene_seq_id'),
                'old_text': best_match.get('text'),
                'character_id': best_match.get('character_id'),
                'source_file': best_match.get('source_file'),
                'match_type': match_type,
                'classification': classification
            })
        else:
            remaining_entries_pass2.append(new_entry)
    logger.info(f"第一遍完成: 成功匹配 {pass1_success_count} 条。")

    # --- Context Verification Pass ---
    logger.info("\n--- 上下文验证: 检查已匹配项的上下文一致性 ---")
    new_id_to_match_map = {m['new_voice_id']: m for m in matched_data}
    new_id_to_new_entry_map = {e['id']: e for e in new_data} # Assumes new_data is sorted by id

    confirmed_matches = []
    entries_for_rematch = []
    reverted_count = 0

    for match in matched_data:
        new_id = match['new_voice_id']
        scene_id = match.get('old_scene_id')
        scene_seq_id = match.get('old_scene_seq_id')

        if scene_id is None or scene_seq_id is None: # Skip if no scene info
            confirmed_matches.append(match)
            continue

        # --- Check previous voice context ---
        prev_new_entry = new_id_to_new_entry_map.get(new_id - 1)
        prev_match = new_id_to_match_map.get(new_id - 1) if prev_new_entry else None
        
        # Context is OK if: 1. No previous entry. 2. Prev entry is not in the same scene. 3. Prev entry is sequential.
        prev_context_ok = (prev_new_entry is None) or \
                          (prev_match and (
                              prev_match.get('old_scene_id') != scene_id or \
                              prev_match.get('old_scene_seq_id') == scene_seq_id - 1
                          ))

        # --- Check next voice context ---
        next_new_entry = new_id_to_new_entry_map.get(new_id + 1)
        next_match = new_id_to_match_map.get(new_id + 1) if next_new_entry else None

        # Context is OK if: 1. No next entry. 2. Next entry is not in the same scene. 3. Next entry is sequential.
        next_context_ok = (next_new_entry is None) or \
                          (next_match and (
                              next_match.get('old_scene_id') != scene_id or \
                              next_match.get('old_scene_seq_id') == scene_seq_id + 1
                          ))

        inside_context_ok = (next_new_entry is None or prev_new_entry is None or next_match is None or prev_match is None or next_match is None or next_match.get('old_scene_id') != prev_match.get('old_scene_id')) or \
            (prev_match.get('old_scene_seq_id') <= scene_seq_id <= next_match.get('old_scene_seq_id'))

        if prev_context_ok and next_context_ok and inside_context_ok:
            confirmed_matches.append(match)
        else:
            # 仅当候选项不唯一（0或>=2）时，才考虑撤销
            new_text = match['new_text']
            normalized_new_text = normalize_text(new_text)
            # 检查精确匹配和标准化匹配的候选项数量
            num_candidates = len(old_data_map.get(new_text, [])) or len(old_data_normalized_map.get(normalized_new_text, []))

            if num_candidates == 1:
                # 如果只有一个候选项，我们相信这个匹配是正确的，不撤销
                confirmed_matches.append(match)
                logger.debug(f"  - 保留匹配 (唯一候选项): New ID {match['new_voice_id']} ({match['new_text']})")
            else:
                # Revert match and send for re-matching
                logger.debug(f"  - 撤销匹配: New ID {match['new_voice_id']} ({match['new_text']}) <-> Old ID {match['old_voice_id']} ({match['old_text']})")
                reverted_count += 1
                original_new_entry = new_id_to_new_entry_map.get(new_id)
                if original_new_entry:
                    entries_for_rematch.append(original_new_entry)
                # Also remove the used old voice ID to make it available again
                used_old_voice_ids.remove(match['old_voice_id'])

    logger.info(f"上下文验证完成: {reverted_count} 条因上下文不一致被撤销，将重新匹配。")
    matched_data = confirmed_matches
    # Combine Pass 1 failures with reverted entries for the next passes
    remaining_entries_pass2.extend(entries_for_rematch)
    remaining_entries_pass2.sort(key=lambda x: x['id'])

    # --- Pass 2: Contextual Matching for Ambiguous Entries ---
    logger.info("\n--- 第二遍: 对剩余条目中存在歧义的部分执行上下文精确匹配 ---")
    pass2_success_count = 0
    remaining_entries_pass3 = []  # Entries that will go to vector search
    for new_entry in reversed(remaining_entries_pass2):
        new_text = new_entry.get('text', '')
        
        # Find potential candidates from script data for contextual matching
        candidates = old_script_map.get(new_text, [])
        
        # Only perform context match if there's ambiguity (multiple candidates)
        if new_text and len(candidates) > 1:
            found_context_match = False
            for candidate in candidates:

                # Triplet check: current text (already matches), previous, and next context
                if new_entry.get('context_prev', '') == candidate.get('context_prev', '') and \
                   new_entry.get('context_next', '') == candidate.get('context_next', ''):
                    
                    pass2_success_count += 1
                    logger.debug(f"  - 上下文匹配成功: New ID {new_entry['id']}")
                    logger.debug(f"    - New Context: ['{new_entry.get('context_prev', '')}', '{new_entry.get('text', '')}', '{new_entry.get('context_next', '')}']")
                    logger.debug(f"    - Old Context: ['{candidate.get('context_prev', '')}', '{candidate.get('text', '')}', '{candidate.get('context_next', '')}']")

                    used_old_voice_ids.add(candidate['voice_id'])
                    classification = classify_voice_file(f"{new_entry.get('filename')}.wav")
                    matched_data.append({
                        'new_voice_id': new_entry.get('id'),
                        'new_filename': new_entry.get('filename'),
                        'new_text': new_entry['text'],
                        'old_voice_id': candidate.get('voice_id'),
                        'old_scene_id': candidate.get('scene_id'),
                        'old_scene_seq_id': candidate.get('scene_seq_id'),
                        'old_text': candidate.get('text'),
                        'character_id': candidate.get('character_id'),
                        'source_file': candidate.get('source_file'),
                        'match_type': 'context',
                        'classification': classification
                    })
                    found_context_match = True
                    break # Found a match, no need to check other candidates
            
            if not found_context_match:
                remaining_entries_pass3.append(new_entry)
        else:
            # If no ambiguity, pass to the next stage
            remaining_entries_pass3.append(new_entry)
    logger.info(f"第二遍完成: 成功匹配 {pass2_success_count} 条。")

    # --- Pass 3: Vector Similarity Matching ---
    logger.info("\n--- 第三遍: 对剩余条目执行向量相似度匹配 ---")
    pass3_success_count = 0
    for new_entry in remaining_entries_pass3:
        best_match, match_type = find_best_match(new_entry, old_data_map, old_data_normalized_map, old_script_list, model, old_embeddings, args, used_old_voice_ids, methods=['vector'])

        if best_match:
            pass3_success_count += 1
            logger.debug(f"  - 向量相似度匹配成功: New ID {new_entry['id']} {match_type[13:]}")
            logger.debug(f"    - New Context: [{new_entry['context_prev']} {new_entry['text']} {new_entry['context_next']}]")
            logger.debug(f"    - Old Context: [{best_match['context_prev']} {best_match['text']} {best_match['context_next']}]")

            vector_search_success_count += 1
            classification = classify_voice_file(f"{new_entry.get('filename')}.wav")
            matched_data.append({
                'new_voice_id': new_entry.get('id'),
                'new_filename': new_entry.get('filename'),
                'new_text': new_entry['text'],
                'old_voice_id': best_match.get('voice_id'),
                'old_scene_id': best_match.get('scene_id'),
                'old_scene_seq_id': best_match.get('scene_seq_id'),
                'old_text': best_match.get('text'),
                'character_id': best_match.get('character_id'),
                'source_file': best_match.get('source_file'),
                'match_type': match_type,
                'classification': classification
            })
        else:
            unmatched_data.append({
                'new_voice_id': new_entry.get('id'),
                'new_filename': new_entry.get('filename'),
                'text': new_entry['text']
            })
    logger.info(f"第三遍完成: 成功匹配 {pass3_success_count} 条。")

    # 最终成功数就是 matched_data 列表的长度
    success_count = len(matched_data)

    # 在写入前按 new_voice_id 排序
    matched_data.sort(key=lambda x: x['new_voice_id'])

    # 写入输出文件
    with open(MERGED_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(matched_data, f, ensure_ascii=False, indent=4)
    
    with open(UNMATCHED_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(unmatched_data, f, ensure_ascii=False, indent=4)

    # --- 更新 t_voice.json ---
    logger.info("\n正在将匹配结果应用到新的 t_voice.json...")
    
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

        logger.info(f"\n成功更新 {updated_count} 个已匹配的语音条目。")
        if args.map_failed_to_empty:
            logger.info(f"已将 {unmatched_mapped_count} 个未匹配的语音条目指向 EMPTY.wav。")

        # 4. 确保 output 目录存在
        output_dir = 'output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 5. 写入新的 t_voice.json 文件
        output_t_voice_path = os.path.join(output_dir, 't_voice.json')
        with open(output_t_voice_path, 'w', encoding='utf-8') as f:
            json.dump(t_voice_content, f, ensure_ascii=False, indent=4)
        
        logger.info(f"成功更新 {updated_count} 个条目。")
        logger.info(f"新的 t_voice.json 已保存到: {output_t_voice_path}")

    except Exception as e:
        logger.error(f"错误：更新 t_voice.json 失败: {e}")

    # --- 打印统计结果 ---
    logger.info("\n--- 匹配完成 ---")
    logger.info(f"总计 (输入文件): {total_count}")
    logger.info(f"处理 (符合条件): {processed_count}")
    logger.info(f"成功: {success_count} (其中向量搜索: {vector_search_success_count})")
    logger.info(f"失败: {processed_count - success_count}")
    logger.info(f"成功匹配的数据已保存到: {MERGED_OUTPUT_FILE}")
    logger.info(f"未匹配的数据已保存到: {UNMATCHED_OUTPUT_FILE}")

if __name__ == '__main__':
    main()
