# -*- coding: utf-8 -*-
import os
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import colorsys
from date_string import get_time_string, get_now_time

# 配置参数
DATA_DIR = "data"               # 数据存储目录
OUTPUT_HTML = "sector_report.html"  # 输出文件名
MAX_LOOKBACK_DAYS = 10          # 最大回溯天数
DEFAULT_COLOR = "#666666"        # 默认颜色（中灰色）
MIN_LIGHTNESS = 0.1             # 最小亮度（30%）
MAX_LIGHTNESS = 0.6             # 最大亮度（70%）
MIN_SATURATION = 0.4            # 最小饱和度（40%）
MAX_SATURATION = 0.8            # 最大饱和度（80%）

def generate_contrast_color(name, count):
    """生成可控对比度的颜色"""
    if count == 1:
        return DEFAULT_COLOR
    
    # 通过哈希生成稳定色相
    hex_dig = hashlib.md5(name.encode()).hexdigest()[:6]
    r = int(hex_dig[0:2], 16) / 255.0
    g = int(hex_dig[2:4], 16) / 255.0
    b = int(hex_dig[4:6], 16) / 255.0

    # 转换到HSL空间调整亮度和饱和度
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    new_l = max(MIN_LIGHTNESS, min(l, MAX_LIGHTNESS))
    new_s = max(MIN_SATURATION, min(s, MAX_SATURATION))
    
    # 转回RGB
    new_r, new_g, new_b = colorsys.hls_to_rgb(h, new_l, new_s)
    return "#{:02x}{:02x}{:02x}".format(
        int(new_r * 255),
        int(new_g * 255),
        int(new_b * 255)
    )

def find_nearest_file(base_date, prefix):
    """查找有效文件（保持不变）"""
    for i in range(MAX_LOOKBACK_DAYS + 1):
        check_date = (base_date + timedelta(days=i)).strftime("%Y%m%d")
        file_path = os.path.join(DATA_DIR, f"{prefix}_{check_date}.csv")
        if os.path.exists(file_path):
            return check_date, pd.read_csv(file_path)
    return None, None

def load_available_data(max_days=5):
    """精准加载有效数据"""
    end_date = get_now_time()
    valid_dates = set()
    collected_data = {
        "industry": {},
        "concept": {},
        "counts": {"industry": {}, "concept": {}}
    }

    # 从今天开始向前搜索10天范围
    for delta in range(10):
        current_date = end_date - timedelta(days=delta)
        date_str = current_date.strftime("%Y%m%d")
        
        # 行业数据
        industry_path = os.path.join(DATA_DIR, f"industry_{date_str}.csv")
        if os.path.exists(industry_path):
            df = pd.read_csv(industry_path)
            names = df["板块名称"].tolist()[:20]
            collected_data["industry"][date_str] = {
                "names": names,
                "ranks": {name: idx+1 for idx, name in enumerate(names)},
                "changes": {name: f"{df.iloc[idx]['涨跌幅']:.2f}%" for idx, name in enumerate(names)}
            }
            valid_dates.add(date_str)
            # 精确统计出现次数
            for name in names:
                collected_data["counts"]["industry"][name] = collected_data["counts"]["industry"].get(name, 0) + 1

        # 概念数据
        concept_path = os.path.join(DATA_DIR, f"concept_{date_str}.csv")
        if os.path.exists(concept_path):
            df = pd.read_csv(concept_path)
            names = df["板块名称"].tolist()[:20]
            collected_data["concept"][date_str] = {
                "names": names,
                "ranks": {name: idx+1 for idx, name in enumerate(names)},
                "changes": {name: f"{df.iloc[idx]['涨跌幅']:.2f}%" for idx, name in enumerate(names)}
            }
            valid_dates.add(date_str)
            for name in names:
                collected_data["counts"]["concept"][name] = collected_data["counts"]["concept"].get(name, 0) + 1

        # 达到最大所需天数时停止
        if len(valid_dates) >= max_days:
            break

    # 生成排序后的日期列表（从早到晚）
    sorted_dates = sorted(valid_dates, key=lambda x: datetime.strptime(x, "%Y%m%d"))[-max_days:]
    return {
        "industry": {k: v for k, v in collected_data["industry"].items() if k in sorted_dates},
        "concept": {k: v for k, v in collected_data["concept"].items() if k in sorted_dates},
        "dates": sorted_dates,
        "counts": collected_data["counts"]
    }

def generate_html_report(data):
    """生成修复后的HTML报告"""
    industry_data = data["industry"]
    concept_data = data["concept"]
    date_list = data["dates"]
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>板块追踪报告（修复版）</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; min-width: 120px; position: sticky; top: 0; }}
            .rank-change {{ font-size: 0.8em; color: #666; }}
            .positive {{ color: #e74c3c; }}
            .negative {{ color: #2ecc71; }}
            .date-header {{ cursor: help; border-bottom: 2px solid #999; }}
            @media (max-width: 768px) {{ th, td {{ padding: 4px; font-size: 0.9em; }} }}
        </style>
    </head>
    <body>
        <h2>行业板块追踪（共{len(date_list)}天）</h2>
        {generate_table(industry_data, date_list, data["counts"]["industry"])}
        <h2>概念板块追踪（共{len(date_list)}天）</h2>
        {generate_table(concept_data, date_list, data["counts"]["concept"])}
    </body>
    </html>
    """
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

def generate_table(data_dict, date_list, count_dict):
    """生成独立统计的表格"""
    table = '<div style="overflow-x: auto;">\n<table>\n<tr><th>排名</th>'
    
    # 生成表头
    for date_str in date_list:
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        display_date = date_obj.strftime("%m-%d")
        full_date = date_obj.strftime("%Y-%m-%d")
        table += f'<th class="date-header" title="{full_date}">{display_date}</th>'
    table += "</tr>\n"
    
    # 生成数据行
    for rank in range(20):
        table += "<tr>"
        table += f"<td>{rank+1}</td>"
        
        prev_ranks = {}
        for date_str in date_list:
            current_data = data_dict.get(date_str, {})
            names = current_data.get("names", [])
            changes = current_data.get("changes", {})
            ranks = current_data.get("ranks", {})
            
            if rank < len(names):
                name = names[rank]
                count = count_dict.get(name, 0)  # 使用对应类别的统计字典
                color = generate_contrast_color(name, count)
                
                # 计算名次变化
                rank_change = ""
                if prev_ranks:
                    prev_rank = prev_ranks.get(name)
                    if prev_rank is not None:
                        change = prev_rank - (rank+1)
                        symbol = "+" if change > 0 else ""
                        style_class = "positive" if change > 0 else "negative" if change < 0 else ""
                        rank_change = f'<span class="rank-change {style_class}">({symbol}{change})</span>'
                
                cell = f'<span style="color:{color}">{name}</span> '
                cell += f'<span class="change">{changes.get(name, "")}</span>{rank_change}'
                prev_ranks = ranks
            else:
                cell = ""
                prev_ranks = {}
                
            table += f"<td>{cell}</td>"
            
        table += "</tr>\n"
    return table + "</table>\n</div>"

if __name__ == "__main__":
    # 修改返回值处理
    data = load_available_data(max_days=5)
    if not data:
        print("错误：没有找到有效数据文件")
    else:
        generate_html_report(data)
        print(f"报告已生成：{os.path.abspath(OUTPUT_HTML)}")