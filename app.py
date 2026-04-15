import streamlit as st
import pandas as pd
import re
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="설비 실시간 검색 시스템", layout="wide")

# --- 커스텀 스타일 ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #eee; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; border: 1px solid #eee; }
    .project-header { font-size: 1.2rem; font-weight: bold; color: #007bff; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 유틸리티 함수
def get_val(df, r, c):
    try:
        if r < df.shape[0] and c < df.shape[1]:
            val = df.iloc[r, c]
            return "" if pd.isna(val) or str(val).strip().lower() == 'nan' else str(val).strip()
    except: return ""
    return ""

def extract_num(val):
    try:
        n = re.sub(r'[^0-9.]', '', str(val).replace(',', ''))
        return float(n) if n else 0
    except: return 0

def check_multi_filter(selected_list, row_val, basic_list):
    if not selected_list: return True
    if "없음" in selected_list and (row_val == "" or row_val == "0"): return True
    if "기타" in selected_list and (row_val != "" and not any(x in row_val for x in basic_list)): return True
    return any(x in row_val for x in selected_list if x not in ["없음", "기타"])

# 3. 메인 로직
st.title("📂 실시간 설비 프로젝트 검색")

# 파일 업로드 (사이드바)
uploaded_file = st.sidebar.file_uploader("📊 엑셀 파일 업로드 (xlsx, csv)", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        # 데이터 로드
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, header=None)
        else:
            df = pd.read_excel(uploaded_file, header=None)
        
        # --- 사이드바 필터 (변경 즉시 결과 반영) ---
        st.sidebar.header("🔍 검색 조건")
        
        loc_list = ["서울", "인천", "경기", "대전", "광주", "대구", "부산", "세종", "강원"]
        v_loc = st.sidebar.selectbox("📍 위치", ["전체"] + loc_list + ["기타"])
        
        year_list = [str(y) for y in range(2020, 2027)]
        v_year = st.sidebar.selectbox("📅 년도", ["전체"] + year_list + ["기타"])
        
        hvac_list = ["개별가스", "지역난방", "중앙난방", "EHP"]
        v_hvac = st.sidebar.selectbox("🔥 냉난방방식", ["전체"] + hvac_list + ["기타"])
        
        v_unit = st.sidebar.selectbox("🏘️ 세대수", ["전체", "100세대 미만", "101~300세대", "301~500세대", "501~1000세대", "1001~2000세대", "2001~3000세대", "3001세대 이상"])
        
        type_list = ["공동주택", "주상복합", "오피스텔", "리모델링"]
        v_type = st.sidebar.selectbox("🏢 건물유형", ["전체"] + type_list + ["기타"])
        
        fire_list = ["소방포함/ 성능위주", "소방포함/ 비성능위주", "소방제외/ 성능위주", "소방제외/ 비성능위주"]
        v_fire = st.sidebar.selectbox("🚒 소방여부", ["전체"] + fire_list + ["기타"])

        spec_list = ["우수처리", "중수처리", "연료전지", "지열", "정화조", "사우나", "음식물", "쓰레기", "수영장"]
        v_specs = st.sidebar.multiselect("✨ 특화설비", ["없음", "기타"] + spec_list)
        
        note_list = ["지하단차", "초고층", "준초고층", "진출입", "산악", "공항", "지하철"]
        v_notes = st.sidebar.multiselect("⚠️ 특수사항", ["없음", "기타"] + note_list)

        # --- 필터링 로직 실행 ---
        found_data = []
        # D열(3번 인덱스)부터 끝까지 2칸씩 이동하며 검사
        for j in range(3, df.shape[1], 2):
            p_name = get_val(df, 0, j)
            if not p_name or "Unnamed" in p_name: continue
            
            # 행별 데이터 추출
            row_year = get_val(df, 3, j)
            row_hvac = get_val(df, 4, j)
            row_type = get_val(df, 5, j)
            row_fire = get_val(df, 5, j+1)
            row_unit = extract_num(get_val(df, 6, j)) + extract_num(get_val(df, 7, j))
            row_area = extract_num(get_val(df, 13, j))
            row_spec = get_val(df, 46, j)
            row_note = get_val(df, 48, j)

            # 필터 매칭 여부 (선택 안함 = 전체 = 무조건 True)
            m_loc = (v_loc == "전체") or (v_loc in p_name if v_loc != "기타" else not any(x in p_name for x in loc_list))
            m_year = (v_year == "전체") or (v_year in row_year if v_year != "기타" else not any(x in row_year for x in year_list))
            m_hvac = (v_hvac == "전체") or (v_hvac in row_hvac if v_hvac != "기타" else not any(x in row_hvac for x in hvac_list))
            m_type = (v_type == "전체") or (v_type in row_type if v_type != "기타" else not any(x in row_type for x in type_list))
            
            # 소방 판정
            f_in, p_in = "소방" in row_fire, "성능" in row_fire
            if v_fire == "전체": m_fire = True
            elif v_fire == "소방포함/ 성능위주": m_fire = f_in and p_in
            elif v_fire == "소방포함/ 비성능위주": m_fire = f_in and not p_in
            elif v_fire == "소방제외/ 성능위주": m_fire = not f_in and p_in
            elif v_fire == "소방제외/ 비성능위주": m_fire = not f_in and not p_in
            else: m_fire = not (f_in or
