import streamlit as st
import pandas as pd
import re
from io import BytesIO

# 1. 페이지 설정 및 테마
st.set_page_config(page_title="설비 비교 프로젝트 선정", layout="wide", initial_sidebar_state="expanded")

# --- 스타일 정의 ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .filter-container { background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; margin-bottom: 20px; }
    .project-card { border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; margin-bottom: 10px; background-color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# 2. 유틸리티 함수
def get_val(df, r, c):
    try:
        if r < df.shape[0] and c < df.shape[1]:
            val = df.iloc[r, c]
            if pd.isna(val) or str(val).strip().lower() == 'nan':
                return ""
            return str(val).strip()
    except:
        return ""
    return ""

def extract_num(val):
    try:
        n = re.sub(r'[^0-9.]', '', str(val).replace(',', ''))
        return float(n) if n else 0
    except:
        return 0

def check_multi_filter(selected_list, row_val, basic_list):
    """중복 선택 필터 로직 (하나라도 포함되면 True)"""
    if not selected_list: return True
    if "없음" in selected_list and (row_val == "" or row_val == "0"): return True
    if "기타" in selected_list and (row_val != "" and not any(x in row_val for x in basic_list)): return True
    return any(x in row_val for x in selected_list if x not in ["없음", "기타"])

# 3. 메인 화면
st.title("📂 설비 비교 프로젝트 선정 시스템")
st.info("💡 엑셀 파일을 업로드하고 좌측 또는 상단의 필터를 설정하여 프로젝트를 검색하세요.")

uploaded_file = st.file_uploader("📊 '비교프로젝트_설비' 파일을 업로드해주세요", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        # 데이터 로드 (캐싱을 통해 성능 향상 가능)
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, header=None)
        else:
            df = pd.read_excel(uploaded_file, header=None)
        
        st.success(f"✅ 데이터를 성공적으로 불러왔습니다. (총 {int((df.shape[1]-3)/2)}개 프로젝트 로드됨)")

        # --- 필터 UI 섹션 ---
        with st.container():
            st.markdown('<div class="filter-container">', unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            
            loc_list = ["서울", "인천", "경기", "대전", "광주", "대구", "부산", "세종", "강원"]
            with col1: v_loc = st.selectbox("📍 위치", ["전체"] + loc_list + ["기타"])
            
            year_list = [str(y) for y in range(2020, 2028)]
            with col2: v_year = st.selectbox("📅 년도", ["전체"] + year_list + ["기타"])
            
            hvac_list = ["개별가스", "지역난방", "중앙난방", "EHP"]
            with col3: v_hvac = st.selectbox("🔥 냉난방방식", ["전체"] + hvac_list + ["기타"])
            
            with col4: v_unit = st.selectbox("🏘️ 세대수", ["전체", "100세대 미만", "101~300세대", "301~500세대", "501~1000세대", "1001~2000세대", "2001~3000세대", "3001세대 이상"])
            
            col5, col6, col7 = st.columns(3)
            type_list = ["공동주택", "주상복합", "오피스텔", "리모델링"]
            with col5: v_type = st.selectbox("🏢 건물유형", ["전체"] + type_list + ["기타"])
            
            area_range_list = ["~30000", "30001~50000", "50001~70000", "70001~100000", "100001~200000", "200001~"]
            with col6: v_area = st.selectbox("📐 연면적(평)", ["전체"] + area_range_list + ["기타"])
            
            fire_list = ["소방포함/ 성능위주", "소방포함/ 비성능위주", "소방제외/ 성능위주", "소방제외/ 비성능위주"]
            with col7: v_fire = st.selectbox("🚒 소방여부", ["전체"] + fire_list + ["기타"])

            spec_list = ["우수처리", "중수처리", "연료전지", "지열", "정화조", "사우나", "음식물", "쓰레기", "수영장"]
            v_specs = st.multiselect("✨ 특화설비 (중복선택 가능)", ["없음", "기타"] + spec_list)
            
            note_list = ["지하단차", "초고층", "준초고층", "진출입", "산악", "공항", "지하철"]
            v_notes = st.multiselect("⚠️ 특수사항 (중복선택 가능)", ["없음", "기타"] + note_list)
            st.markdown('</div>', unsafe_allow_html=True)

        # 4. 검색 실행
        search_btn = st.button("🚀 조건에 맞는 프로젝트 조회")

        if search_btn:
            found_indices = []
            for j in range(3, df.shape[1], 2):
                p_name = get_val(df, 0, j)
                if not p_name or "Unnamed" in p_name: continue
                
                # 데이터 추출
                row_year = get_val(df, 3, j)
                row_hvac = get_val(df, 4, j)
                row_type = get_val(df, 5, j)
                row_fire = get_val(df, 5, j+1)
                row_unit = extract_num(get_val(df, 6, j)) + extract_num(get_val(df, 7, j))
                row_area = extract_num(get_val(df, 13, j))
                row_spec = get_val(df, 46, j)
                row_note = get_val(df, 48, j)

                # --- 판정 로직 ---
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
                else: m_fire = not (f_in or p_in)

                # 면적/세대수 판정
                m_unit = True
                if v_unit != "전체":
                    if "100세대 미만" in v_unit: m_unit = row_unit < 100
                    elif "101~300" in v_unit: m_unit = 101 <= row_unit <= 300
                    elif "301~500" in v_unit: m_unit = 301 <= row_unit <= 500
                    elif "501~1000" in v_unit: m_unit = 501 <= row_unit <= 1000
                    elif "1001~2000" in v_unit: m_unit = 1001 <= row_unit <= 2000
                    elif "2001~3000" in v_unit: m_unit = 2001 <= row_unit <= 3000
                    else: m_unit = row_unit >= 3001

                m_area = True
                if v_area != "전체":
                    if v_area == "기타": m_area = row_area == 0
                    elif "~30000" in v_area: m_area = row_area <= 30000
                    elif "30001~50000" in v_area: m_area = 30001 <= row_area <= 50000
                    elif "50001~70000" in v_area: m_area = 50001 <= row_area <= 70000
                    elif "70001~100000" in v_area: m_area = 70001 <= row_area <= 100000
                    elif "100001~200000" in v_area: m_area = 100001 <= row_area <= 200000
                    else: m_area = row_area > 200000

                # 다중 선택 로직 적용
                m_spec = check_multi_filter(v_specs, row_spec, spec_list)
                m_note = check_multi_filter(v_notes, row_note, note_list)

                if all([m_loc, m_year, m_hvac, m_unit, m_type, m_area, m_fire, m_spec, m_note]):
                    found_indices.append(j)

            # 결과 출력
            if found_indices:
                st.subheader(f"🎯 검색 결과: {len(found_indices)}건")
                
                # --- 결과 다운로드 기능 추가 ---
                # 검색된 컬럼들만 추출하여 엑셀 생성
                output_columns = [0, 1] + [idx for i in found_indices for idx in (i, i+1)]
                filtered_df = df.iloc[:50, output_columns]
                
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    filtered_df.to_excel(writer, index=False, header=False, sheet_name='Search_Result')
                
                st.download_button(
                    label="📥 검색 결과 엑셀 다운로드",
                    data=output.getvalue(),
                    file_name="project_search_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                st.write("---")

                for col in found_indices:
                    with st.expander(f"📌 {get_val(df, 0, col)} (상세보기)"):
                        html = """
                        <table style="width:100%; border-collapse:collapse; font-size:13px; border: 1px solid #ddd;">
                            <tr style="background-color: #f2f2f2;">
                                <th style="border:1px solid #ddd; padding:8px; width:20%;">항목</th>
                                <th style="border:1px solid #ddd; padding:8px; width:20%;">세부</th>
                                <th style="border:1px solid #ddd; padding:8px; background-color:#eef4ff;">데이터 1</th>
                                <th style="border:1px solid #ddd; padding:8px; background-color:#eef4ff;">데이터 2</th>
                            </tr>
                        """
                        for r in range(49):
                            val1 = get_val(df, r, col)
                            val2 = get_val(df, r, col+1)
                            # 값이 있을 때만 행 생성 (선택 사항)
                            html += f"""
                            <tr>
                                <td style="border:1px solid #ddd; padding:6px; font-weight:bold; background:#fafafa;">{get_val(df,r,0)}</td>
                                <td style="border:1px solid #ddd; padding:6px; color:#666;">{get_val(df,r,1)}</td>
                                <td style="border:1px solid #ddd; padding:6px;">{val1}</td>
                                <td style="border:1px solid #ddd; padding:6px;">{val2}</td>
                            </tr>
                            """
                        st.markdown(html + '</table>', unsafe_allow_html=True)
            else:
                st.warning("🧐 조건에 맞는 프로젝트가 없습니다. 필터를 조정해 보세요.")
                
    except Exception as e:
        st.error(f"⚠️ 시스템 오류가 발생했습니다: {e}")
        st.info("파일 형식이 '비교프로젝트_설비' 양식과 일치하는지 확인해 주세요.")