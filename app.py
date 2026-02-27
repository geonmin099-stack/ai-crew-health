import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression

# 1. 페이지 설정 (아이콘 및 타이틀)
st.set_page_config(page_title="선원 보건 안전 AI", page_icon="⚓", layout="wide")

# 한글 폰트 설정 (윈도우/맥 호환을 위해 설정하지만, 웹 배포 시에는 기본 폰트 사용 권장)
plt.rcParams['axes.unicode_minus'] = False

# 2. 데이터베이스: 수치별 상세 소견 및 선상 관리 방안
HEALTH_GUIDE = {
    "혈압": {
        "정상": {"소견": "혈압이 매우 안정적입니다. 심혈관 건강이 양호합니다.", "관리": "현재의 식습관을 유지하시고, 선내 염분 섭취에 계속 주의하세요."},
        "주의": {"소견": "혈압이 다소 높습니다. 초기 고혈압 단계로 진입할 가능성이 있습니다.", "관리": "국물 요리 섭취를 줄이고, 매일 20분간 선상 스트레칭을 권장합니다."},
        "위험": {"소견": "고혈압 위험군입니다. 뇌심혈관 질환 발생 가능성이 높으므로 정밀 진단이 필요합니다.", "관리": "즉시 선내 상비약을 확인하고, 육상 전문의 진료를 예약하십시오. 금연과 금주는 필수입니다."}
    },
    "혈당": {
        "정상": {"소견": "당 대사가 원활하며 인슐린 저항성이 안정적입니다.", "관리": "정제 탄수화물(간식, 흰 빵) 섭취를 조절하여 현재 상태를 유지하세요."},
        "주의": {"소견": "공복 혈당이 높습니다. 당뇨 전 단계(내당능 장애)일 수 있습니다.", "관리": "식후 15분간 선실 내에서 제자리 걷기를 하여 혈당 수치를 관리하세요."},
        "위험": {"소견": "당뇨병 가능성이 매우 높습니다. 만성 합병증 예방이 시급합니다.", "관리": "식단에서 당분을 즉시 제외하고, 매일 정해진 시간에 혈당을 체크해야 합니다."}
    },
    "간수치": {
        "정상": {"소견": "간 기능이 건강하게 유지되고 있습니다. 해독 능력이 좋습니다.", "관리": "피로 해소를 위해 규칙적인 수면 시간을 확보하세요."},
        "주의": {"소견": "간에 피로가 쌓인 상태입니다. 지방간 혹은 과로 증상일 수 있습니다.", "관리": "충분한 수분 섭취와 함께 간장제 복용을 고려하고 음주를 자제하세요."},
        "위험": {"소견": "간 손상이 우려되는 수치입니다. 간염 혹은 심한 지방간이 의심됩니다.", "관리": "절대 금주가 필요하며, 선장에게 보고 후 업무 강도를 낮추어 휴식을 취해야 합니다."}
    }
}

# 3. 데이터 로드 함수
@st.cache_data
def load_data():
    # [중요] 여기에 본인의 구글 시트 CSV 내보내기 주소를 넣으세요
    SHEET_URL = "https://docs.google.com/spreadsheets/d/e/YOUR_ID/pub?output=csv"
    df = pd.read_csv(SHEET_URL)
    return df

# 4. 메인 화면 구성
st.title("⚓ 선원 보건 안전 AI 리스크 관리 시스템")
st.info("실시간 건강 데이터 분석과 전문가 지식 베이스를 결합한 지능형 보건 관리 솔루션입니다.")

try:
    df = load_data()
    name_list = df['이름'].unique()
    
    # 사이드바 조회
    st.sidebar.header("📋 선원 정보 조회")
    target_name = st.sidebar.selectbox("선원 이름을 선택하세요", name_list)

    if target_name:
        # 데이터 정렬 (검진일 기준)
        user_data = df[df['이름'] == target_name].sort_values('검진일')
        latest_data = user_data.iloc[-1]
        
        # 상단 대시보드 카드
        st.subheader(f"👤 {target_name} 선원 분석 리포트 (최근 검진: {latest_data['검진일']})")
        
        # 분석 로직 (단순 예시이므로 실제 컬럼명에 맞춰 수정 필요)
        summary_results = []
        cols = st.columns(3)
        
        # 항목별 체크 및 카드 출력
        for i, item in enumerate(["혈압", "혈당", "간수치"]):
            val = latest_data[item]
            # 기준값 설정 (예시)
            if item == "혈압": status = "정상" if val < 120 else ("주의" if val < 140 else "위험")
            elif item == "혈당": status = "정상" if val < 100 else ("주의" if val < 126 else "위험")
            else: status = "정상" if val < 40 else ("주의" if val < 60 else "위험")
            
            summary_results.append({"key": item, "status": status, "val": val})
            
            with cols[i]:
                st.metric(label=item, value=val, delta=status, delta_color="inverse" if status != "정상" else "normal")

        st.divider()

        # 5. 상세 전문가 소견 섹션
        st.subheader("👨‍⚕️ 전문가 분석 소견 및 선상 가이드라인")
        
        for res in summary_results:
            key = res['key']
            status = res['status']
            guide = HEALTH_GUIDE[key][status]
            
            with st.expander(f"🔍 {key} 지표 상세 분석 ({status})", expanded=(status == "위험")):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**🩺 의학적 소견**\n\n{guide['소견']}")
                with col_b:
                    st.markdown(f"**⚓ 선상 관리 방안**\n\n{guide['관리']}")

        # 6. 추세 분석 및 미래 예측 그래프
        st.divider()
        st.subheader("📈 건강 추세 분석 및 2년 후 위험도 예측 (Linear Regression)")
        
        selected_metric = st.selectbox("분석할 지표를 선택하세요", ["혈압", "혈당", "간수치"])
        
        fig, ax = plt.subplots(figsize=(10, 4))
        y = user_data[selected_metric].values
        x = np.array(range(len(y))).reshape(-1, 1)
        
        # 선형 회귀 계산
        lr_model = LinearRegression().fit(x, y)
        future_x = np.array([[len(y)], [len(y)+1]])
        future_y = lr_model.predict(future_x)
        
        # 그래프 그리기
        ax.plot(user_data['검진일'], y, marker='o', label='과거 기록', color='#004085', linewidth=2)
        ax.plot(['1회차 후(예측)', '2회차 후(예측)'], future_y, 'r--', marker='x', label='AI 예측 경로')
        ax.set_title(f"{selected_metric} 변화 추이 및 예측", fontsize=12)
        ax.legend()
        st.pyplot(fig)

        if any(r['status'] == "위험" for r in summary_results):
            st.warning("⚠️ 현재 위험 수치가 감지되었습니다. 원격 의료 상담 혹은 하선 후 정밀 검진이 강력히 권고됩니다.")

except Exception as e:
    st.error(f"데이터를 불러올 수 없습니다. 구글 시트 주소와 컬럼명을 확인하세요. (에러: {e})")
