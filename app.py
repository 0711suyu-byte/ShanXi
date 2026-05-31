import streamlit as st
import json
import os
import pandas as pd
import time
import random  # <--- 新增：用于打乱题目顺序
from datetime import timedelta

# ================= 1. 页面高级美化与排版设置 =================
st.set_page_config(page_title="陕西省直遴选备考系统", page_icon="🍏", layout="wide")

st.markdown("""
    <style>
    /* 全局 Apple 风格背景与字体 */
    .stApp { background-color: #F5F5F7; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif; }
    .block-container { max-width: 1000px; padding-top: 2rem; }
    
    /* 圆角白色卡片效果 (通用) */
    .apple-card {
        background-color: #FFFFFF; border-radius: 18px; padding: 32px;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04); margin-bottom: 24px; border: 1px solid #E5E5EA;
    }
    
    /* 主观题：材料与题目框 */
    .material-box { 
        padding: 24px; border-radius: 12px; background-color: #FAFAFA; 
        border: 1px solid #E5E5EA; line-height: 1.8; font-size: 16px; color: #1D1D1F; 
        white-space: pre-wrap; margin-bottom: 20px;
    }
    .question-box { background-color: #F0F8FF; padding: 18px; border-radius: 12px; border-left: 5px solid #007AFF; margin-bottom: 20px; color: #1D1D1F;}
    
    /* 客观题：题干与解析 */
    .q-title { font-size: 20px; font-weight: 600; color: #1D1D1F; line-height: 1.5; margin-bottom: 24px;}
    .explanation-box {
        background-color: #F5F5F7; border-radius: 12px; padding: 20px;
        margin-top: 20px; color: #333333; font-size: 15px; line-height: 1.6; border-left: 4px solid #FF3B30;
    }
    
    /* ================= 选项大按钮化 CSS ================= */
    div[data-testid="stButton"] > button {
        height: auto;
        min-height: 64px; 
        padding: 16px 24px;
        justify-content: flex-start; 
        text-align: left;
        border-radius: 14px;
        border: 1px solid #E5E5EA;
        background-color: #FFFFFF;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
        transition: all 0.2s ease;
        margin-bottom: 12px;
        width: 100%;
    }
    div[data-testid="stButton"] > button div[data-testid="stMarkdownContainer"] p {
        font-size: 17px; 
        color: #1D1D1F;
        text-align: left;
        white-space: normal; 
        line-height: 1.5;
        margin: 0;
    }
    /* 悬停效果 */
    div[data-testid="stButton"] > button:hover {
        border-color: #007AFF;
        background-color: #F0F8FF;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 122, 255, 0.1);
    }
    div[data-testid="stButton"] > button:hover div[data-testid="stMarkdownContainer"] p {
        color: #007AFF;
    }
    /* 导航按钮特殊处理 */
    div[data-testid="stButton"] > button[kind="primary"] {
        justify-content: center;
        background-color: #007AFF;
        border: none;
        min-height: 50px;
        box-shadow: none;
    }
    div[data-testid="stButton"] > button[kind="primary"] div[data-testid="stMarkdownContainer"] p {
        color: #FFFFFF;
        text-align: center;
        font-weight: 600;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background-color: #0056b3;
        transform: none;
    }
    
    /* 计时器样式 */
    .timer-text { font-size: 24px; font-weight: bold; color: #FF3B30; text-align: center; margin-bottom: 20px; font-variant-numeric: tabular-nums;}
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 数据加载函数 (全新层级结构) =================
DATA_DIR = "data"
OBJ_DIR = os.path.join(DATA_DIR, "客观题")
SUBJ_DIR = os.path.join(DATA_DIR, "主观题")

# --- 客观题双层加载逻辑 ---
@st.cache_data
def get_obj_categories():
    """获取客观题的大类文件夹"""
    if not os.path.exists(OBJ_DIR): return []
    return sorted([d for d in os.listdir(OBJ_DIR) if os.path.isdir(os.path.join(OBJ_DIR, d))])

@st.cache_data
def get_obj_modules(category_name):
    """获取某个大类文件夹下的所有 JSON 试卷"""
    category_path = os.path.join(OBJ_DIR, category_name)
    if not os.path.exists(category_path): return []
    return sorted([f.replace('.json', '') for f in os.listdir(category_path) if f.endswith('.json')])

@st.cache_data
def load_obj_questions(category_name, module_name):
    """加载具体的客观题 JSON 数据"""
    file_path = os.path.join(OBJ_DIR, category_name, f"{module_name}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# --- 主观题双层加载逻辑 ---
@st.cache_data
def get_subj_categories():
    if not os.path.exists(SUBJ_DIR): return []
    return sorted([d for d in os.listdir(SUBJ_DIR) if os.path.isdir(os.path.join(SUBJ_DIR, d))])

@st.cache_data
def load_subj_scenarios(category_name):
    category_path = os.path.join(SUBJ_DIR, category_name)
    scenarios = []
    if os.path.exists(category_path):
        files = sorted([f for f in os.listdir(category_path) if f.endswith('.json')])
        for file_name in files:
            file_path = os.path.join(category_path, file_name)
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                scenarios.append(json.load(f))
    return scenarios

# ================= 3. 状态管理初始化 =================
if 'obj_idx' not in st.session_state: st.session_state.obj_idx = 0
if 'obj_wrong' not in st.session_state: st.session_state.obj_wrong = []
if 'obj_show_exp' not in st.session_state: st.session_state.obj_show_exp = False
if 'obj_last_wrong_ans' not in st.session_state: st.session_state.obj_last_wrong_ans = "" 
if 'start_time' not in st.session_state: st.session_state.start_time = time.time()
if 'current_questions' not in st.session_state: st.session_state.current_questions = []

if 'subj_step' not in st.session_state: st.session_state.subj_step = 0
if 'subj_last_id' not in st.session_state: st.session_state.subj_last_id = None

# ================= 4. 侧边栏与全局导航 =================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Emblem_of_Shaanxi.svg/120px-Emblem_of_Shaanxi.svg.png", width=60)
    st.title("🎯 遴选全能题库")
    
    app_mode = st.radio("切换学习模式", ["📚 客观题专项演练", "🏛️ 主观题深度剖析"], label_visibility="collapsed")
    st.divider()

# ================= 5. 分支逻辑：客观题模式 =================
if app_mode == "📚 客观题专项演练":
    with st.sidebar:
        obj_categories = get_obj_categories()
        if not obj_categories:
            st.warning(f"请在 {OBJ_DIR} 文件夹下建立分类文件夹（如'模块1'）并放入 JSON 题库")
            st.stop()
            
        # 第一层：选择考点大类
        selected_category = st.selectbox("📁 选择考点大类", obj_categories)
        
        obj_modules = get_obj_modules(selected_category)
        if not obj_modules:
            st.warning("该分类下暂无试卷文件，请放入 JSON 文件。")
            st.stop()
            
        # 第二层：选择具体试卷
        selected_module = st.selectbox("📄 选择演练试卷", obj_modules)
        
        # 倒计时模块 (修改为 480 秒，即 8 分钟)
        st.divider()
        elapsed = time.time() - st.session_state.start_time
        remaining = max(0, 480 - elapsed)
        st.markdown(f"<div class='timer-text'>⏱ {str(timedelta(seconds=int(remaining)))}</div>", unsafe_allow_html=True)
        
        # 错题本模块
        st.divider()
        st.markdown("### 📝 错题记忆系统")
        st.metric(label="已收集错题", value=f"{len(st.session_state.obj_wrong)} 道")
        if st.session_state.obj_wrong:
            df_wrong = pd.DataFrame(st.session_state.obj_wrong)
            st.download_button("⬇️ 导出错题本 (CSV)", data=df_wrong.to_csv(index=False).encode('utf-8-sig'), file_name="客观错题本.csv", mime="text/csv", type="primary")

    # 检测是否切换了试卷，如果切换了，重置进度、【倒计时】并【随机打乱题目】
    if ('last_obj_cat' not in st.session_state or st.session_state.last_obj_cat != selected_category or 
        'last_obj_mod' not in st.session_state or st.session_state.last_obj_mod != selected_module):
        
        st.session_state.obj_idx = 0
        st.session_state.obj_show_exp = False
        st.session_state.last_obj_cat = selected_category
        st.session_state.last_obj_mod = selected_module
        st.session_state.start_time = time.time() # 自动重置倒计时
        
        # 加载并随机打乱题目顺序
        raw_questions = load_obj_questions(selected_category, selected_module)
        shuffled_qs = list(raw_questions) # 拷贝一份，避免修改原数据缓存
        random.shuffle(shuffled_qs)
        st.session_state.current_questions = shuffled_qs
        
        st.rerun() # 刷新页面应用重置

    questions = st.session_state.get('current_questions', [])
    if not questions: st.stop()

    total_q = len(questions)
    q_data = questions[st.session_state.obj_idx]
    q_id = q_data.get('id', str(st.session_state.obj_idx))
    correct_ans = q_data['correct_answer']

    st.title(f"📚 {selected_module}")
    st.markdown(f"<span style='color:#86868B; font-size:14px;'>进度：{st.session_state.obj_idx + 1} / {total_q}</span>", unsafe_allow_html=True)
    st.progress((st.session_state.obj_idx + 1) / total_q)

    # 题目与选项卡片
    st.markdown("<div class='apple-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='q-title'>{st.session_state.obj_idx + 1}. {q_data['question']}</div>", unsafe_allow_html=True)
    
    options = q_data['options']
    
    for opt in options:
        if st.button(opt, key=f"btn_{q_id}_{opt}"):
            is_correct = opt.startswith(correct_ans)
            
            if is_correct:
                if st.session_state.obj_idx < total_q - 1:
                    st.session_state.obj_idx += 1
                    st.session_state.obj_show_exp = False
                else:
                    st.toast("🎉 恭喜你，本套试卷已全部刷完！", icon="👏")
                    st.session_state.obj_show_exp = False
                st.rerun()
                
            else:
                st.session_state.obj_show_exp = True
                st.session_state.obj_last_wrong_ans = opt
                
                # 记录错题，增加“大类”字段
                if not any(wq['id'] == q_id for wq in st.session_state.obj_wrong):
                    st.session_state.obj_wrong.append({
                        "id": q_id, 
                        "模块分类": selected_category,
                        "试卷名称": selected_module, 
                        "题目": q_data['question'], 
                        "你的答案": opt, 
                        "正确答案": correct_ans, 
                        "解析": q_data['explanation']
                    })
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # 错题解析展示
    if st.session_state.obj_show_exp:
        st.error(f"❌ 刚才选错了（你的答案：{st.session_state.obj_last_wrong_ans[:1]}）。正确答案是：**{correct_ans}**")
        st.markdown(f"<div class='explanation-box'><strong>💡 深度解析：</strong><br><br>{q_data['explanation']}</div>", unsafe_allow_html=True)

    # 底部导航控制
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.session_state.obj_idx > 0:
            if st.button("⬅️ 上一题", use_container_width=True):
                st.session_state.obj_idx -= 1
                st.session_state.obj_show_exp = False
                st.rerun()

    with col3:
        if st.session_state.obj_show_exp and st.session_state.obj_idx < total_q - 1:
            if st.button("下一题 ➡️", type="primary", use_container_width=True):
                st.session_state.obj_idx += 1
                st.session_state.obj_show_exp = False
                st.rerun()

# ================= 6. 分支逻辑：主观题模式 =================
elif app_mode == "🏛️ 主观题深度剖析":
    with st.sidebar:
        subj_categories = get_subj_categories()
        if not subj_categories:
            st.warning(f"请在 {SUBJ_DIR} 文件夹下建立分类并放入大题 JSON 文件")
            st.stop()
            
        selected_category = st.selectbox("📂 选择考点大类", subj_categories)
        scenarios = load_subj_scenarios(selected_category)
        if not scenarios: st.stop()
            
        scenario_titles = [s.get('title', '未命名题目') for s in scenarios]
        selected_s_name = st.selectbox("📝 选择大题", scenario_titles)
        current_scenario = scenarios[scenario_titles.index(selected_s_name)]

    if st.session_state.subj_last_id != current_scenario.get('id'):
        st.session_state.subj_step = 0
        st.session_state.subj_last_id = current_scenario.get('id')

    def go_next_subj():
        if st.session_state.subj_step < 3: st.session_state.subj_step += 1
    def go_reset_subj(): st.session_state.subj_step = 0

    st.title(f"🏛️ 专项突破：{selected_category}")
    st.subheader(f"📖 {current_scenario.get('title', '未命名')}")
    
    steps_guide = ["1. 深度剖析长材料", "2. 穿透材料抓题眼", "3. 解析核心采分点", "4. 拆解标准答案"]
    st.progress((st.session_state.subj_step + 1) * 25, text=f"**当前状态：{steps_guide[st.session_state.subj_step]}**")

    sub_questions = current_scenario.get('sub_questions', [])

    st.markdown("<div class='apple-card'>", unsafe_allow_html=True)
    if st.session_state.subj_step == 0:
        st.markdown("### 📄 给定材料 (全真模拟)")
        st.markdown(f"<div class='material-box'>{current_scenario.get('materials_plain', '')}</div>", unsafe_allow_html=True)
    elif st.session_state.subj_step == 1:
        st.markdown("### 🔍 题眼会诊 (沙里淘金思维训练)")
        st.markdown(f"<div class='material-box'>{current_scenario.get('materials_annotated', '')}</div>", unsafe_allow_html=True)
    elif st.session_state.subj_step >= 2:
        st.markdown("### 💯 核心采分点" if st.session_state.subj_step == 2 else "### 🏆 标准规范参考答案")
        if not sub_questions:
            st.warning("本题没有配置子问题。")
        else:
            tabs = st.tabs([f"题 {i+1}：{sq.get('type', '主观题')}" for i, sq in enumerate(sub_questions)])
            for i, tab in enumerate(tabs):
                sq = sub_questions[i]
                with tab:
                    st.markdown(f"<div class='question-box'><strong>【题目】</strong>{sq.get('question', '')}<br><br><strong>【要求】</strong>{sq.get('requirements', '')}</div>", unsafe_allow_html=True)
                    if st.session_state.subj_step == 2: st.markdown(sq.get('scoring_points', '暂无采分点'), unsafe_allow_html=True)
                    elif st.session_state.subj_step == 3: st.markdown(sq.get('reference_answer', '暂无答案'), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.subj_step == 0: st.button("🔍 第一步：开启『题眼红字高亮』", on_click=go_next_subj, type="primary", use_container_width=True)
        elif st.session_state.subj_step == 1: st.button("💡 第二步：查看『采分点』", on_click=go_next_subj, type="primary", use_container_width=True)
        elif st.session_state.subj_step == 2: st.button("📄 第三步：查看『完整参考答案』", on_click=go_next_subj, type="primary", use_container_width=True)
        elif st.session_state.subj_step == 3: st.button("🔄 重新推演本大题", on_click=go_reset_subj, use_container_width=True)