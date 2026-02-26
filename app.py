import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import re

# 1. 한글 설정 (웹 배포 환경 대응)
plt.rc('font', family='NanumGothic')
plt.rcParams['axes.unicode_minus'] = False

# 2. 기준 데이터 설정
CRITERIA_MAP = {
    "Glucose": {"label": "Glucose (혈당)", "safe_high": 99, "warn_high": 125, "advice": {"안전": "공복 혈당 정상입니다.", "경계": "당뇨 전 단계 주의.", "위험": "고혈당 진단 필요."}, "risk_scenario": "당직 중 집중력 장애 리스크."},
    "AST(GOT)": {"label": "AST (간수치)", "safe_high": 40, "warn_high": 80, "advice": {"안전": "양호합니다.", "경계": "피로 누적 주의.", "위험": "간 손상 위험."}, "risk_scenario": "긴급 상황 대응력 감소."},
    "ALT(GPT)": {"label": "ALT (지방간)", "safe_high": 40, "warn_high": 80, "advice": {"안전": "양호합니다.", "경계": "초기 지방간 주의.", "위험": "지방간염 위험."}, "risk_scenario": "업무 효율 저하."},
    "r-GTP(감마-GTP)": {"label": "r-GTP (알코올)", "safe_high": 63, "warn_high": 100, "advice": {"안전": "양호합니다.", "경계": "음주 관리 필요.", "위험": "간 손상 주의."}, "risk_scenario": "무기력증."},
    "T.Cholesterol(총콜레스테롤)": {"label": "T.Cholesterol", "safe_high": 199, "warn_high": 239, "advice": {"안전": "양호.", "경계": "식단 주의.", "위험": "심혈관 위험."}, "risk_scenario": "심근경색 위험."},
    "Hemoglobin(혈색소)": {"label": "혈색소", "safe_low": 13, "safe_high": 17, "warn_low": 11, "warn_high": 18, "advice": {"안전": "양호.", "경계": "철분 권장.", "위험": "빈혈 주의."}, "risk_scenario": "실족 사고 위험."},
    "W.B.C(백혈구수)": {"label": "백혈구", "safe_high": 10, "warn_high": 12, "advice": {"안전": "양호.", "경계": "면역 관리.", "위험": "염증 의심."}, "risk_scenario": "집단 감염 위험."}
}

# 3. 데이터 로드 함수 (들여쓰기 수정 완료)
def load_data_from_google_sheet(name):
    sheet_url = "https://docs.google.com/spreadsheets/d/1EOpOWv83_7Bfkhzw1o78OlVYhdLAEAh5KbFdmtsyl6E/export?format=xlsx"
    try:
        xls = pd.ExcelFile(sheet_url)
        target_sheet = next((s for s in xls.sheet_names if name.replace(" ", "") in s.replace(" ", "")), None)
        if not target_sheet: return None
        
        raw = pd.read_excel(xls, sheet_name=target_sheet, header=None)
        df = pd.read_excel(xls, sheet_name=target_sheet, skiprows=2)
        years = raw.iloc[0, 2:8].dropna().astype(str).str.replace("년", "").tolist()
        
        res_data = {}
        for key in CRITERIA_MAP.keys():
            s_name = key.split('(')[0]
            row = df[df.iloc[:, 1].astype(str).str.contains(s_name, na=False, case=False)]
            if not row.empty:
                vals = pd.to_numeric(row.iloc[0, 2:2+len(years)], errors='coerce').fillna(0).tolist()
                res_data[key] = {"values": vals}
        return {"years": years, "data": res_data, "sheet_name": target_sheet}
    except Exception as e:
        return None

# 4. 앱 UI 레이아웃
st.set_page_config(page_title="선원 보건 안전 AI", layout="wide")
st.title("⚓ 선원 보건 안전 AI 관리 시스템")

with st.sidebar:
    st.header("📋 데이터 입력")
    search_name = st.text_input("분석 성명", placeholder="예: 홍길동")
    btn = st.button("분석 실행", use_container_width=True)

if btn and search_name:
    res = load_data_from_google_sheet(search_name)
    if res:
        st.success(f"✅ {res['sheet_name']}님의 데이터를 불러왔습니다.")
        # 간략 분석 결과 출력
        for key, content in res['data'].items():
            vals = [v for v in content['values'] if v > 0]
            if vals:
                st.write(f"**{CRITERIA_MAP[key]['label']}**: {vals[-1]}")
    else:
        st.error("해당 성명을 찾을 수 없습니다. 구글 시트의 탭 이름을 확인하세요.")
