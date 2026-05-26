import streamlit as st
import json
import os

# ================= 1. 页面高级美化与排版设置 =================
st.set_page_config(page_title="陕西省直遴选主观题模拟", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    .reportview-container .main .block-container{ max-width: 1100px; }
    .material-box { 
        padding: 30px; 
        border-radius: 12px; 
        background-color: #fcfcfc; 
        border: 1px solid #e2e8f0; 
        line-height: 1.8; 
        font-size: 16px; 
        color: #1a202c; 
        white-space: pre-wrap;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 50px; font-size: 16px !important;}
    .question-box { background-color: #f0f7ff; padding: 15px; border-left: 5px solid #0066cc; margin-bottom: 20px;}
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 核心功能：读取多层级题库 =================
DATA_DIR = "data"

@st.cache_data
def get_categories():
    """扫描 data 文件夹下的所有子文件夹，作为考点大类"""
    if not os.path.exists(DATA_DIR):
        return []
    categories = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
    return sorted(categories)

@st.cache_data
def load_scenarios_from_folder(category_name):
    """读取某个大类文件夹下的所有单题(大题) JSON 文件"""
    category_path = os.path.join(DATA_DIR, category_name)
    scenarios = []
    
    if os.path.exists(category_path):
        files = sorted([f for f in os.listdir(category_path) if f.endswith('.json')])
        for file_name in files:
            file_path = os.path.join(category_path, file_name)
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    q_data = json.load(f)
                    scenarios.append(q_data)
            except Exception as e:
                st.error(f"⚠️ 读取文件 {file_name} 时出错: {e}")
    return scenarios

# ================= 3. 侧边栏：大类与题目导航 =================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Emblem_of_Shaanxi.svg/120px-Emblem_of_Shaanxi.svg.png", width=80)
    st.title("📚 遴选全真题库")
    
    categories = get_categories()
    
    if not categories:
        st.error(f"⚠️ 找不到题库！请确保建好了 '{DATA_DIR}' 文件夹及其子分类文件夹。")
        st.stop()

    # 下拉菜单1：选择大类
    selected_category = st.selectbox("📂 选择考点大类", categories)
    
    # 动态加载大题
    scenarios = load_scenarios_from_folder(selected_category)
    
    if not scenarios:
        st.warning("该分类下暂无题目，请放入JSON文件。")
        st.stop()
        
    # 下拉菜单2：选择大题场景
    scenario_titles = [f"{s.get('title', '未命名题目')}" for s in scenarios]
    selected_s_name = st.selectbox("📝 选择要演练的大题", scenario_titles)
    
    selected_s_idx = scenario_titles.index(selected_s_name)
    current_scenario = scenarios[selected_s_idx]

# ================= 4. 状态管理 =================
# 当切换大题时，自动将步骤重置为0
if 'last_seen_s' not in st.session_state or st.session_state.last_seen_s != current_scenario.get('id'):
    st.session_state.step = 0
    st.session_state.last_seen_s = current_scenario.get('id', 'temp_id')

def go_next():
    if st.session_state.step < 3:
        st.session_state.step += 1

def go_reset():
    st.session_state.step = 0

# ================= 5. 右侧主界面渲染 =================
st.title(f"🏛️ 专项突破：{selected_category}")
st.subheader(f"📖 {current_scenario.get('title', '未命名')}")
st.divider()

steps_guide = ["1. 深度剖析长材料", "2. 穿透材料抓题眼", "3. 解析核心采分点", "4. 拆解标准参考答案"]
st.progress((st.session_state.step + 1) * 25, text=f"**当前复习状态：{steps_guide[st.session_state.step]}**")
st.markdown("---")

# 获取子题目列表
sub_questions = current_scenario.get('sub_questions', [])

# ----------------- 步骤 0 & 1：展示材料 -----------------
if st.session_state.step == 0:
    st.markdown("### 📄 给定材料 (全真模拟)")
    st.markdown(f"<div class='material-box'>{current_scenario.get('materials_plain', '')}</div>", unsafe_allow_html=True)
    
elif st.session_state.step == 1:
    st.markdown("### 🔍 题眼会诊 (沙里淘金思维训练)")
    st.markdown(f"<div class='material-box'>{current_scenario.get('materials_annotated', '')}</div>", unsafe_allow_html=True)

# ----------------- 步骤 2 & 3：使用 Tabs 展示多道小题 -----------------
elif st.session_state.step >= 2:
    if st.session_state.step == 2:
        st.markdown("### 💯 阅卷老干部的核心采分点")
    else:
        st.markdown("### 🏆 陕西省直机关标准规范参考答案")
        
    # 如果没有小题数据，给出提示
    if not sub_questions:
        st.warning("本题没有配置子问题 (sub_questions)。")
    else:
        # 动态生成标签页 (例如：问题一：归纳概括, 问题二：提出对策...)
        tab_titles = [f"题 {i+1}：{sq.get('type', '主观题')}" for i, sq in enumerate(sub_questions)]
        tabs = st.tabs(tab_titles)
        
        # 遍历每一个标签页，往里面填充对应小题的内容
        for i, tab in enumerate(tabs):
            sq = sub_questions[i]
            with tab:
                # 顶部的题目要求框
                st.markdown(f"""
                <div class='question-box'>
                    <strong>【题目】</strong>{sq.get('question', '')}<br><br>
                    <strong>【要求】</strong>{sq.get('requirements', '')}
                </div>
                """, unsafe_allow_html=True)
                
                # 根据当前步骤展示采分点或完整答案
                if st.session_state.step == 2:
                    st.success(sq.get('scoring_points', '暂无采分点说明'))
                elif st.session_state.step == 3:
                    st.markdown(sq.get('reference_answer', '暂无参考答案'), unsafe_allow_html=True)

st.markdown("---")

# ================= 6. 交互控制按键 =================
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.session_state.step == 0:
        st.button("🔍 第一步：开启『题眼红字高亮』", on_click=go_next, type="primary")
    elif st.session_state.step == 1:
        st.button("💡 第二步：查看『三道小题采分点』", on_click=go_next, type="primary")
    elif st.session_state.step == 2:
        st.button("印发公文 📄 第三步：查看『完整参考答案』", on_click=go_next, type="primary")
    elif st.session_state.step == 3:
        st.button("🔄 重新推演本大题", on_click=go_reset)