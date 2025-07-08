import pandas as pd
import os

# 路径配置
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
FILES = [f"jn091{i}.csv" for i in range(2, 9)]
OUTPUT_PATH = os.path.join(DATA_DIR, "cleaned_data.csv")

# 每次读取的块大小（按行数）
CHUNK_SIZE = 100_000

# 写入头部标志
is_first_chunk = True

for filename in FILES:
    path = os.path.join(DATA_DIR, filename)
    print(f"正在处理: {path}")

    try:
        # 分块读取
        for chunk in pd.read_csv(path, encoding='utf-8', low_memory=False, chunksize=CHUNK_SIZE):
            # 删除 filter 列
            if 'filter_$' in chunk.columns:
                chunk.drop(columns=['filter_$'], inplace=True)

            # 删除重复和关键字段空值
            chunk.drop_duplicates(inplace=True)
            chunk.dropna(subset=['COMMADDR', 'UTC', 'LAT', 'LON'], inplace=True)

            # 类型转换
            chunk['LAT'] = pd.to_numeric(chunk['LAT'], errors='coerce')
            chunk['LON'] = pd.to_numeric(chunk['LON'], errors='coerce')
            chunk['HEAD'] = pd.to_numeric(chunk['HEAD'], errors='coerce')
            chunk['SPEED'] = pd.to_numeric(chunk['SPEED'], errors='coerce')

            chunk.dropna(subset=['LAT', 'LON', 'SPEED'], inplace=True)

            # 时间转换
            chunk['UTC'] = pd.to_datetime(chunk['UTC'], unit='s', errors='coerce', utc=True)

            # 2. 删除无法解析的 UTC 时间
            chunk.dropna(subset=['UTC'], inplace=True)

            # 3. 将 UTC 时间转换为 'Asia/Shanghai' (北京时间)
            chunk['BJTime'] = chunk['UTC'].dt.tz_convert('Asia/Shanghai')


            # 设置载客状态
            def map_status(flag):
                try:
                    flag = int(flag)
                    if flag == 268435456:
                        return '载客'
                    elif flag == 0:
                        return '空载'
                    else:
                        return '异常'
                except:
                    return '未知'


            chunk['状态'] = chunk['TFLAG'].apply(map_status)

            # 字段筛选
            out_cols = ['COMMADDR', 'UTC', 'LAT', 'LON', 'HEAD', 'SPEED', 'TFLAG', 'BJTime', '状态']
            chunk = chunk[out_cols]

            # 写入到文件（首块写 header，其余块 append）
            chunk.to_csv(OUTPUT_PATH, mode='a', index=False, header=is_first_chunk)
            is_first_chunk = False  # 后续块不写 header

    except Exception as e:
        print(f"处理文件 {filename} 出错：{e}")
