# -*- coding: utf-8 -*-
import akshare as ak
import pandas as pd
import os
import matplotlib.pyplot as plt
from date_string import get_time_string

# 配置全局中文字体（以微软雅黑为例）
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 设置非交互式后端（避免GUI依赖）
plt.switch_backend('Agg')  # 关键配置：解决Windows环境依赖问题

def get_sector_data():
    """获取并处理行业/概念板块数据"""
    # 行业板块处理
    industry_df = ak.stock_board_industry_name_em()
    industry_clean = industry_df[~industry_df["板块名称"].str.contains("昨日")]
    industry_top = industry_clean.sort_values("涨跌幅", ascending=False)

    # 概念板块处理
    concept_df = ak.stock_board_concept_name_em()
    concept_clean = concept_df[~concept_df["板块名称"].str.contains("昨日")]
    concept_top = concept_clean.sort_values("涨跌幅", ascending=False)
    
    return industry_top, concept_top

def save_full_data(industry_df, concept_df):
    """保存全量字段数据"""
    today = get_time_string()
    
    # 确保 data 文件夹存在
    os.makedirs("data", exist_ok=True)
    
    # 保存行业数据（保留所有字段）
    industry_df.to_csv(
        f"data/industry_{today}.csv", 
        encoding="utf_8_sig",
        index=False
    )
    
    # 保存概念数据（保留所有字段）
    concept_df.to_csv(
        f"data/concept_{today}.csv",
        encoding="utf_8_sig",
        index=False
    )

def add_labels(ax, bars):
    """通用标签添加函数（复用代码）"""
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height,
                f'{height:.2f}%', 
                ha='center', va='bottom')

def generate_subplot_charts(industry_df, concept_df):
    """生成子图对比视图"""
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), dpi=150)  # 网页5、网页10
    
    # ========== 行业子图 ==========
    bars1 = ax1.bar(
        industry_df["板块名称"], 
        industry_df["涨跌幅"],
        color='#1f77b4',
        label='行业'
    )
    add_labels(ax1, bars1)  # 复用标签添加逻辑
    ax1.set_title("行业板块涨幅TOP20", pad=20)
    
    # ========== 概念子图 ==========
    bars2 = ax2.bar(
        concept_df["板块名称"], 
        concept_df["涨跌幅"],
        color='#ff7f0e',
        label='概念'
    )
    add_labels(ax2, bars2)
    ax2.set_title("概念板块涨幅TOP20", pad=20)
    
    # ========== 全局优化 ==========
    for ax in [ax1, ax2]:
        ax.tick_params(axis='x', rotation=45)
        ax.set_ylabel("涨跌幅 (%)")

    os.makedirs("img", exist_ok=True)
    
    plt.suptitle(f"板块涨幅对比 ({get_time_string()})", y=0.98)  # 网页7
    plt.tight_layout()
    plt.savefig(f"img/sector_comparison_{get_time_string()}.png")
    plt.close()  # 释放内存

if __name__ == "__main__":
    # 数据获取
    industry_data, concept_data = get_sector_data()
    
    # 全量数据存储
    save_full_data(industry_data, concept_data)
    
    print("开始生成图表")
    # 可视化输出
    generate_subplot_charts(industry_data.head(20), concept_data.head(20))  # 生成子图对比视图
    
    print("执行完成：数据已存储为CSV文件，图表已生成PNG文件")