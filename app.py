import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="설비 검색 시스템 진단모드", layout="wide")

st.title("📂 실시간 설비 프로젝트 검색 (진단 모드)")

# 1. 파일 업로드
uploaded_file = st.sidebar.file_uploader("📊 엑셀 파일을 올려주세요", type=['xlsx', 'csv'])

if uploaded_file:
    try:
        # 데이터 로드
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, header=None).fillna("")
        else:
            df = pd.read_excel(uploaded_file, header=None).fillna("")

        # [진단] 데이터가 어떻게 생겼는지 상단에 노출 (나중에 삭제 가능)
        with st.expander("🔍 [진단] 업로드된 데이터 미리보기 (처음 10행/10열)"):
            st.write(df.iloc[:10, :10])
            st.info("💡 위 표의 0행에 프로젝트명이 있고, 3행에 년도, 4행에 방식이 있는지 확인하세요.")

        # --- 필터 설정 ---
        st.sidebar.header("🔍 검색 조건")
        
        # 위치 필터 (직접 입력도 가능하게 변경)
        v_loc = st.sidebar.text_input("📍 위치 검색 (예: 서울, 경기 / 비워두면 전체)", "")
        
        v_hvac = st.sidebar.selectbox("🔥 냉난방방식", ["전체", "개별가스", "지역난방", "중앙난방", "EHP"])
        
        v_type = st.sidebar.selectbox("🏢 건물유형", ["전체", "공동주택", "주상복합", "오피스텔", "리모델링"])

        # --- 검색 로직 ---
        found_data = []
        
        # D열(3번)부터 2칸씩 이동
        for j in range(3, df.shape[1], 2):
            # 데이터 추출 시 공백 제거 및 문자열 변환
            p_name = str(df.iloc[0, j]).strip()
            
            # 빈 칸이나 제목 없는 칸 건너뛰기
            if not p_name or "Unnamed" in p_name or p_name == "":
                continue
            
            # 비교용 데이터 추출 (행 위치가 다르면 여기서 조정!)
            row_year = str(df.iloc[3, j]).strip()
            row_hvac = str(df.iloc[4, j]).strip()
            row_type = str(df.iloc[5, j]).strip()
            
            # 필터 매칭 여부 (전체일 땐 무조건 True)
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
            
            # 요약 표
            st.dataframe(res_df.drop(columns=['index']), use_container_width=True, hide_index=True)
            
            # 상세보기
            selected_p = st.selectbox("🔍 상세 내용을 볼 프로젝트 선택", ["선택하세요"] + res_df['프로젝트명'].tolist())
            if selected_p != "선택하세요":
                p_idx = res_df[res_df['프로젝트명'] == selected_p]['index'].values[0]
                
                # 표 그리기
                html = '<table style="width:100%; border-collapse:collapse; font-size:12px; border: 1px solid #ddd;">'
                # 0~48행까지 출력
                for r in range(min(50, len(df))):
                    html += f"""
                    <tr>
                        <td style="border:1px solid #ddd; padding:5px; font-weight:bold; background:#f1f3f5; width:20%;">{str(df.iloc[r,0])}</td>
                        <td style="border:1px solid #ddd; padding:5px; color:#666; width:20%;">{str(df.iloc[r,1])}</td>
                        <td style="border:1px solid #ddd; padding:5px; width:30%;">{str(df.iloc[r,p_idx])}</td>
                        <td style="border:1px solid #ddd; padding:5px; width:30%;">{str(df.iloc[r,p_idx+1])}</td>
                    </tr>"""
                st.markdown(html + '</table>', unsafe_allow_html=True)
        else:
            st.warning("🧐 일치하는 결과가 없습니다. 필터를 모두 '전체'로 두거나 검색어를 확인해 보세요.")
            st.info("💡 만약 '전체'인데도 안 나온다면, 엑셀의 프로젝트명이 0행(첫 번째 줄)이 아닌 다른 곳에 있을 수 있습니다.")

    except Exception as e:
        st.error(f"⚠️ 오류 발생: {e}")
else:
    st.info("👈 왼쪽에서 엑셀 파일을 업로드해 주세요.")
