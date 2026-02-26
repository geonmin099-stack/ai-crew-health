import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import re
import altair as alt

# 폰트 및 한글 설정
plt.rc('font', family='NanumGothic')
plt.rcParams['axes.unicode_minus'] = False

# [원형 유지] 기존 분석 기준 및 조언 데이터맵
CRITERIA_MAP = {
    "Glucose": {"label": "Glucose (혈당)", "safe_high": 99, "warn_high": 125, "advice": {"안전": "공복 혈당 정상입니다.", "경계": "당뇨 전 단계 주의.", "위험": "고혈당 진단 필요."}, "risk_scenario": "당직 중 집중력 장애 리스크."},
    "AST(GOT)": {"label": "AST (간수치)", "safe_high": 40, "warn_high": 80, "advice": {"안전": "양호합니다.", "경계": "피로 누적 주의.", "위험": "간 손상 위험."}, "risk_scenario": "긴급 상황 대응력 감소."},
    "ALT(GPT)": {"label": "ALT (지방간)", "safe_high": 40, "warn_high": 80, "advice": {"안전": "양호합니다.", "경계": "초기 지방간 주의.", "위험": "지방간염 위험."}, "risk_scenario": "업무 효율 저하."},
    "r-GTP(감마-GTP)": {"label": "r-GTP (알코올)", "safe_high": 63, "warn_high": 100, "advice": {"안전": "양호합니다.", "경계": "음주 관리 필요.", "위험": "간 손상 주의."}, "risk_scenario": "무기력증."},
    "T.Cholesterol(총콜레스테롤)": {"label": "T.Cholesterol", "safe_high": 199, "warn_high": 239, "advice": {"안전": "양호.", "경계": "식단 주의.", "위험": "심혈관 위험."}, "risk_scenario": "심근경색 위험."},
    "Hemoglobin(혈색소)": {"label": "혈색소", "safe_low": 13, "safe_high": 17, "warn_low": 11, "warn_high": 18, "advice": {"안전": "양호.", "경계": "철분 권장.", "위험": "빈혈 주의."}, "risk_scenario": "실족 사고 위험."},
    "W.B.C(백혈구수)": {"label": "백혈구", "safe_high": 10, "warn_high": 12, "advice": {"안전": "양호.", "경계": "면역 관리.", "위험": "염증 의심."}, "risk_scenario": "집단 감염 위험."}
}

# [경로 교체] 로컬 파일 경로 대신 구글 시트 URL 사용
def load_data_from_google_sheet(name):
    # 실제 연동할 구글 시트 주소
    sheet_url = "https://docs.google.com/spreadsheets/d/1EOpOWv83_7Bfkhzw1o78OlVYhdLAEAh5KbFdmtsyl6E/export?format=xlsx"
    try:
        xls = pd.ExcelFile(sheet_url)
        # 이름과 일치하는 시트 탭 찾기
        target_sheet = next((s for s in xls.sheet_names if name.replace(" ", "") in s.replace(" ", "")), None)
        if not target_sheet:
            return None
        
        raw = pd.read_excel(xls, sheet_name=target_sheet, header=None)
        df = pd.read_excel(xls, sheet_name=target_sheet, skiprows=2)
        
        # [원형 유지] 기존 엑셀 분석 로직
        years_list = raw.iloc[0, 2:8].dropna().astype(str).str.replace("년", "").tolist()
        doc_note = ""
        note_row = raw.iloc[20:25, 0:10].dropna() # 기존 비고란 위치
        if not note_row.empty:
            doc_note = str(note_row.iloc[0,0])

        res_data = {}
        for key in CRITERIA_MAP.keys():
            search_name_key = key.split('(')[0]
            row = df[df.iloc[:, 1].astype(str).str.contains(search_name_key, na=False, case=False)]
            if not row.empty:
                vals = pd.to_numeric(row.iloc[0, 2:2+len(years_list)], errors='coerce').fillna(0).tolist()
                res_data[key] = {"values": vals}
        
        return {"years": years_list, "data": res_data, "doc_note": doc_note, "sheet_name": target_sheet}
    except Exception as e:
        st.error(f"데이터 연동 오류: {e}")
        return None

# [원형 유지] 기존 UI 및 결과 표시 로직
st.set_page_config(page_title="선원 보건 안전 AI", layout="wide")
st.title("⚓ 선원 보건 안전 AI 리스크 관리 시스템")

with st.sidebar:
    st.header("📋 데이터 입력")
    search_name = st.text_input("분석 성명", placeholder="예: 홍길동")
    btn = st.button("분석 실행", use_container_width=True)

if btn and search_name:
    res = load_data_from_google_sheet(search_name)
    if res:
        st.success(f"✅ {res['sheet_name']}님의 데이터를 분석합니다.")
        
        # [원형 유지] 기존의 상세 리스트 및 조언 출력 부분
        for key, content in res['data'].items():
            vals = [v for v in content['values'] if v > 0]
            if not vals: continue
            
            last_val = vals[-1]
            crit = CRITERIA_MAP[key]
            
            # 위험도 판별 로직 (기본 버전 유지)
            status = "안전"
            if "safe_low" in crit:
                if last_val < crit["warn_low"] or last_val > crit["warn_high"]: status = "위험"
                elif last_val < crit["safe_low"] or last_val > crit["safe_high"]: status = "경계"
            else:
                if last_val > crit["warn_high"]: status = "위험"
                elif last_val > crit["safe_high"]: status = "경계"
            
            # 출력 부분
            st.subheader(f"{crit['label']}: {last_val}")
            st.write(f"**진단:** {crit['advice'][status]}")
            if status != "안전":
                st.warning(f"⚠️ **예상 리스크:** {crit['risk_scenario']}")
            
            # 그래프 (기존 matplotlib 스타일 유지)
            fig, ax = plt.subplots(figsize=(10, 2))
            ax.plot(res['years'][:len(content['values'])], content['values'], marker='o', color='navy')
            st.pyplot(fig)
            st.write("---")
            
        if res['doc_note']:
            st.info(f"📝 **종합 소견:** {res['doc_note']}")
    else:
        st.error("성명을 찾을 수 없습니다. 시트의 탭 이름을 확인하세요.")
