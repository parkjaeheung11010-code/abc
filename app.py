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
            else: m_fire = not (f_in or p_in)

            # 세대수 판정
            m_unit = True
            if v_unit != "전체":
                if "100세대 미만" in v_unit: m_unit = row_unit < 100
                elif "101~300" in v_unit: m_unit = 101 <= row_unit <= 300
                elif "301~500" in v_unit: m_unit = 301 <= row_unit <= 500
                elif "501~1000" in v_unit: m_unit = 501 <= row_unit <= 1000
                elif "1001~2000" in v_unit: m_unit = 1001 <= row_unit <= 2000
                elif "2001~3000" in v_unit: m_unit = 2001 <= row_unit <= 3000
                else: m_unit = row_unit >= 3001

            m_spec = check_multi_filter(v_specs, row_spec, spec_list)
            m_note = check_multi_filter(v_notes, row_note, note_list)

            # 최종 판정
            if all([m_loc, m_year, m_hvac, m_unit, m_type, m_fire, m_spec, m_note]):
                found_data.append({
                    "index": j,
                    "프로젝트명": p_name,
                    "년도": row_year,
                    "세대수": int(row_unit),
                    "연면적": row_area,
                    "냉난방": row_hvac
                })

        # --- 결과 화면 ---
        if found_data:
            res_df = pd.DataFrame(found_data)
            
            # 요약 지표
            col1, col2, col3 = st.columns(3)
            col1.metric("검색 결과", f"{len(found_data)} 건")
            col2.metric("평균 세대수", f"{int(res_df['세대수'].mean())} 세대")
            col3.metric("평균 연면적", f"{res_df['연면적'].mean():,.0f} 평")
            
            # 리스트와 상세보기
            st.write("---")
            st.subheader("📋 검색된 프로젝트 목록")
            
            # 간결한 표로 보여주기
            st.dataframe(res_df.drop(columns=['index']), use_container_width=True, hide_index=True)
            
            # 상세 정보 선택
            st.write("---")
            selected_p = st.selectbox("🔍 상세 내용을 보려면 프로젝트를 선택하세요", ["선택하세요"] + res_df['프로젝트명'].tolist())
            
            if selected_p != "선택하세요":
                p_idx = res_df[res_df['프로젝트명'] == selected_p]['index'].values[0]
                
                # 상세 데이터 테이블 생성
                st.markdown(f"<p class='project-header'>📌 {selected_p} 상세 제원</p>", unsafe_allow_html=True)
                html = '<table style="width:100%; border-collapse:collapse; font-size:12px; border: 1px solid #ddd;">'
                for r in range(49):
                    html += f"""
                    <tr>
                        <td style="border:1px solid #ddd; padding:5px; font-weight:bold; background:#f1f3f5; width:20%;">{get_val(df,r,0)}</td>
                        <td style="border:1px solid #ddd; padding:5px; color:#666; width:20%;">{get_val(df,r,1)}</td>
                        <td style="border:1px solid #ddd; padding:5px; width:30%;">{get_val(df,r,p_idx)}</td>
                        <td style="border:1px solid #ddd; padding:5px; width:30%;">{get_val(df,r,p_idx+1)}</td>
                    </tr>"""
                st.markdown(html + '</table>', unsafe_allow_html=True)

            # 결과 다운로드 버튼
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                target_cols = [0, 1] + [d['index'] for d in found_data] + [d['index']+1 for d in found_data]
                df.iloc[:50, sorted(list(set(target_cols)))].to_excel(writer, index=False, header=False)
            
            st.sidebar.download_button(
                label="📥 현재 결과 다운로드 (Excel)",
                data=output.getvalue(),
                file_name="search_results.xlsx",
                mime="application/vnd.ms-excel"
            )
        else:
            st.warning("🧐 일치하는 프로젝트가 없습니다. 필터를 조정해 보세요.")

    except Exception as e:
        st.error(f"⚠️ 데이터 처리 중 오류가 발생했습니다: {e}")
else:
    st.info("👈 왼쪽 사이드바에서 엑셀 파일을 업로드하면 바로 검색이 시작됩니다.")
