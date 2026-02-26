import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import re
import altair as alt  # 에러 방지를 위한 추가

# 1. 한글 폰트 설정 (웹 배포 환경용)
plt.rc('font', family='NanumGothic')
plt.rcParams['axes.unicode_minus'] = False

# 2. 보건 분석 기준 데이터
CRITERIA_MAP = {
    "Glucose": {"label": "Glucose (혈당)", "safe_high": 99, "warn_high": 125, "advice": {"안전": "정상 범위입니다.", "경계": "당뇨 전 단계 주의.", "위험": "고혈당 관리 필요."}},
    "AST(GOT)": {"label": "AST (간수치)", "safe_high": 40, "warn_high": 80, "advice": {"안전": "양호합니다.", "경계": "피로 누적 주의.", "위험": "간 기능 정밀 검사 권고."}},
    "ALT(GPT)": {"label": "ALT (지방간)", "safe_high": 40, "warn_high": 80, "advice": {"안전": "정상입니다.", "경계": "초기 지방간 주의.", "위험": "지방간염 위험."}},
    "r-GTP(감마-GTP)": {"label": "r-GTP (알코올)", "safe_high": 63, "warn_high": 100, "advice": {"안전": "양호.", "경계": "잦은 음주 주의.", "위험": "알코올성 간 손상 주의."}},
    "T.Cholesterol(총콜레스테롤)": {"label": "총콜레스테롤", "safe_high": 199, "warn_high": 239, "advice": {"안전": "양호.", "경계": "식단 조절 필요.", "위험": "동맥경화 주의."}},
    "Hemoglobin(혈색소)": {"label": "Hemoglobin (혈색소)", "safe_low": 13, "safe_high": 17, "warn_low": 11, "warn_high": 18, "advice": {"안전": "정상.", "경계": "철분 섭취 권장.", "위험": "빈혈 관리 필요."}},
    "W.B.C(백혈구수)": {"label": "W.B.C (백혈구)", "safe_high": 10, "warn_high": 12, "advice": {"안전": "정상.", "경계": "면역력 관리 필요.", "위험": "염증 의심."}}
}

# 3. 구글 시트 데이터 로드 함수
def load_data_from_google_sheet(name):
    # 사용자님의 구글 시트 주소
    sheet_url = "https://docs.google.com/spreadsheets/d/1EOpOWv83_7Bfkhzw1o78OlVYhdLAEAh5KbFdmtsyl6E/export?format=xlsx"
    try:
        xls = pd.ExcelFile(sheet_url)
        target_sheet = next((s for s in xls.sheet_names if name.replace(" ", "") in s.replace(" ", "")), None)
        if not target_sheet:
            return None
        
        raw = pd.read_excel(xls, sheet_name=target_sheet, header=None)
        df = pd.read_excel(xls, sheet_name=target_sheet, skiprows=2)
        
        # 연도 추출 (1행 3열부터 8열까지)
        years_list = raw.iloc[0, 2:8].dropna().astype(str).str.replace("년", "").tolist()
        
        res_data = {}
        for key in CRITERIA_MAP.keys():
            search_name_key = key.split('(')[0]
            row = df[df.iloc[:, 1].astype(str).str.contains(search_name_key, na=False, case=False)]
            if not row.empty:
                vals = pd.to_numeric(row.iloc[0, 2:2+len(years_list)], errors='coerce').fillna(0).tolist()
                res_data[key] = {"values": vals}
        
        return {"years": years_list, "data": res_data, "sheet_name": target_sheet}
    except Exception as e:
        st.error(f"⚠️ 데이터 로딩 에러: {e}")
        return None

# 4. 웹 앱 메인 화면 구성
st.set_page_config(page_title="선원 보건 안전 AI", layout="wide")
st.title("⚓ 선원 보건 안전 AI 리스크 관리 시스템")

with st.sidebar:
    st.header("📋 데이터 분석")
    search_name = st.text_input("분석할 성명을 입력하세요", placeholder="예: 양승덕")
    btn = st.button("분석 실행", use_container_width=True)

if btn and search_name:
    res = load_data_from_google_sheet(search_name)
    if res:
        st.success(f"✅ {res['sheet_name']}님의 건강 검진 데이터를 분석합니다.")
        
        # 결과 대시보드 표시
        cols = st.columns(2)
        for i, (key, content) in enumerate(res['data'].items()):
            with cols[i % 2]:
                with st.expander(f"📊 {CRITERIA_MAP[key]['label']}", expanded=True):
                    current_val = content['values'][-1]
                    st.metric(label="최근 수치", value=current_val)
                    
                    # 간단한 그래프 생성
                    chart_data = pd.DataFrame({
                        '연도': res['years'],
                        '수치': content['values']
                    })
                    st.line_chart(chart_data.set_index('연도'))
    else:
        st.error(f"🔍 '{search_name}'님에 해당하는 탭을 시트에서 찾을 수 없습니다.")
