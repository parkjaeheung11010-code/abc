import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="설비 검색 시스템", layout="wide")

st.title("📂 실시간 설비 프로젝트 검색")

# 1. 파일 업로드
uploaded_file = st.sidebar.file_uploader("📊 엑셀 파일을 올려주세요", type=['xlsx', 'csv'])

if uploaded_file:
    try:
        # 데이터 로드 (모든 데이터는 문자열로 처리하여 오류 방지)
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, header=None).fillna("")
        else:
            df = pd.read_excel(uploaded_file, header=None).fillna("")

        # [진단] 데이터 확인용 (문제 해결 후 주석 처리 가능)
        with st.expander("🔍 [진단] 엑셀 데이터 위치 확인"):
            st.write(df.iloc[:10, :10])
            st.info("💡 현재 설정: 프로젝트명(3번 행), 년도(6번 행), 방식(7번 행)을 읽고 있습니다.")

        # --- 사이드바 필터 ---
        st.sidebar.header("🔍 검색 조건")
        v_loc = st.sidebar.text_input("📍 위치 검색 (예: 서울, 경기)", "")
        v_hvac = st.sidebar.selectbox("🔥 냉난방방식", ["전체", "개별가스", "지역난방", "중앙난방", "EHP"])
        v_type = st.sidebar.selectbox("🏢 건물유형", ["전체", "공동주택", "주상복합", "오피스텔", "리모델링"])

        # --- 검색 로직 ---
        found_data = []
        
        # 데이터는 D열(인덱스 3)부터 2칸씩 반복됨
        for j in range(3, df.shape[1], 2):
            # 사용자의 요청에 따라 프로젝트명을 3번 행(인덱스 3)에서 가져옴
            p_name = str(df.iloc[3, j]).strip()
            
            # 빈 칸이나 제목 없는 칸 건너뛰기
            if not p_name or "Unnamed" in p_name or p_name == "":
                continue
            
            # 다른 데이터들도 프로젝트명 위치(3번) 기준으로 3칸씩 아래로 조정
            row_year = str(df.iloc[6, j]).strip()    # 기존 3번 -> 6번 행
            row_hvac = str(df.iloc[7, j]).strip()    # 기존 4번 -> 7번 행
            row_type = str(df.iloc[8, j]).strip()    # 기존 5번 -> 8번 행
            
            # 필터 조건 (입력값이 있을 때만 작동)
            m_loc = True if not v_loc else (v_loc in p_name)
            m_hvac = True if v_hvac == "전체" else (v_hvac in row_hvac)
            m_type = True if v_type == "전체" else (v_type in row_type)

            if m_loc and m_hvac and m_type:
                found_data.append({
                    "index": j,
                    "프로젝트명": p_name,
                    "년도": row_year,
                    "냉난방": row_hvac,
                    "유형": row_type
                })

        # --- 결과 표시 ---
        if found_data:
            res_df = pd.DataFrame(found_data)
            st.success(f"🎯 총 {len(found_data)}개의 프로젝트를 찾았습니다!")
            
            # 요약 리스트
            st.dataframe(res_df.drop(columns=['index']), use_container_width=True, hide_index=True)
            
            # 상세 제원 보기
            st.write("---")
            selected_p = st.selectbox("🔍 상세 내용을 볼 프로젝트 선택", ["선택하세요"] + res_df['프로젝트명'].tolist())
            
            if selected_p != "선택하세요":
                p_idx = res_df[res_df['프로젝트명'] == selected_p]['index'].values[0]
                
                st.subheader(f"📌 {selected_p} 상세 데이터")
                html = '<table style="width:100%; border-collapse:collapse; font-size:12px; border: 1px solid #ddd;">'
                # 데이터가 3번행부터 시작하므로 3번행부터 끝까지 표시
                for r in range(3, len(df)):
                    val1 = str(df.iloc[r, p_idx]).strip()
                    val2 = str(df.iloc[r, p_idx+1]).strip()
                    # 한 행이라도 데이터가 있는 경우만 표시
                    if val1 or val2:
                        html += f"""
                        <tr>
                            <td style="border:1px solid #ddd; padding:5px; font-weight:bold; background:#f1f3f5; width:20%;">{str(df.iloc[r,0])}</td>
                            <td style="border:1px solid #ddd; padding:5px; color:#666; width:20%;">{str(df.iloc[r,1])}</td>
                            <td style="border:1px solid #ddd; padding:5px; width:30%;">{val1}</td>
                            <td style="border:1px solid #ddd; padding:5px; width:30%;">{val2}</td>
                        </tr>"""
                st.markdown(html + '</table>', unsafe_allow_html=True)
        else:
            st.warning("🧐 일치하는 결과가 없습니다. 필터를 조정하거나 엑셀 파일의 3번 행을 확인해 보세요.")

    except Exception as e:
        st.error(f"⚠️ 오류 발생: {e}")
else:
    st.info("👈 왼쪽에서 엑셀 파일을 업로드해 주세요.")
