import pandas as pd
from collections import Counter

# 定义输入和输出文件名
input_csv = 'match_result.csv'
output_csv = 'voice_id_mapping.csv'

# 读取CSV文件
df = pd.read_csv(input_csv)

# 筛选数据：跳过所有MatchType为unmatched或skipped，或者OldVoiceFilename为空的项
df.dropna(subset=['OldVoiceFilename'], inplace=True)
df = df[~df['MatchType'].isin(['unmatched', 'skipped'])]

# 提取OldVoiceFilename的[2:5]作为OldVoiceCharacterId
df['OldVoiceCharacterId'] = df['OldVoiceFilename'].str[2:5]

# print df ['RemakeVoiceCharacterId', 'OldVoiceCharacterId']
print(df[['RemakeVoiceCharacterId', 'OldVoiceCharacterId']])
# 按RemakeVoiceCharacterId分组，并找到最匹配的OldVoiceCharacterId
mapping = {}
for char_id, group in df.groupby('RemakeVoiceCharacterId'):
    # 统计当前分组中OldVoiceCharacterId的出现次数
    id_counts = Counter(group['OldVoiceCharacterId'])
    # 打印统计结果
    print(f"Character ID {char_id}: {id_counts}")
    # 找到出现次数最多的ID
    if id_counts:
        most_common_id = id_counts.most_common(1)[0][0]
        mapping[char_id] = most_common_id

# 将映射关系转换为DataFrame
mapping_df = pd.DataFrame(list(mapping.items()), columns=['RemakeVoiceCharacterId', 'OldVoiceCharacterId'])

# 格式化ID为3位0填充整数，同时保留空值
mapping_df['RemakeVoiceCharacterId'] = pd.to_numeric(mapping_df['RemakeVoiceCharacterId'], errors='coerce').apply(
    lambda x: f'{int(x):03d}' if pd.notna(x) else ''
)
mapping_df['OldVoiceCharacterId'] = mapping_df['OldVoiceCharacterId'].apply(
    lambda x: f'{x}' if pd.notna(x) else ''
)

# 保存到新的CSV文件
mapping_df.to_csv(output_csv, index=False)


print(f"成功生成ID映射文件: {output_csv}")
