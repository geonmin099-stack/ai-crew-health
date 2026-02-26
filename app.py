import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import re
import os

# 1. 페이지 설정
st.set_page_config(page_title="선원 보건 안전 AI 리스크 관리", layout="wide")

# 2. 그래프 한글 깨짐 방지 설정
def set_korean_font():
    paths = [
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
        '/usr/share/fonts/nanumfont/NanumGothic.ttf',
        'NanumGothic.ttf' 
    ]
    font_found = False
    for path in paths:
        if os.path.exists(path):
            fe = fm.FontEntry(fname=path, name='NanumGothic')
            fm.fontManager.ttflist.insert(0, fe)
            plt.rc('font', family='NanumGothic')
            font_found = True
            break
    if not font_found:
        plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False

set_korean_font()

# [CRITERIA_MAP 데이터 동일]
CRITERIA_MAP = {
    "Glucose": {"label": "Glucose (혈당)", "safe_high": 99, "warn_high": 125, "advice": {"안전": "공복 혈당이 정상 범위 내에 있으며 대사 기능이 매우 원활합니다.", "경계": "당뇨 전 단계 수준입니다. 식단 관리와 유산소 운동이 필수적입니다.", "위험": "고혈당 상태로 당뇨병 합병증 진행 위험이 큽니다. 전문의 진단이 필요합니다."}, "trend_bad": "상승", "risk_scenario": "당직 중 급격한 혈당 변화로 인한 의식 혼탁 및 집중력 장애 리스크."},
    "AST(GOT)": {"label": "AST (간수치:피로)", "safe_high": 40, "warn_high": 80, "advice": {"안전": "간 세포 손상 징후가 없으며 에너지 대사가 양호합니다.", "경계": "과로나 수면 부족으로 간 세포가 자극받은 상태입니다. 충분한 휴식을 권고합니다.", "위험": "활동성 간염이나 간 손상이 진행 중입니다. 전신 무력감이 동반될 수 있습니다."}, "trend_bad": "상승", "risk_scenario": "만성 피로 누적으로 인한 반응 속도 저하 및 긴급 상황 대응 능력 감소."},
    "ALT(GPT)": {"label": "ALT (간수치:지방간)", "safe_high": 40, "warn_high": 80, "advice": {"안전": "지방간 위험이 낮으며 간의 해독 작용이 정상입니다.", "경계": "초기 비알코올성 지방간이 우려됩니다. 체중 관리와 식단 조절이 필요합니다.", "위험": "지방간염 또는 약물성 간 손상 가능성이 높습니다. 전문의 진찰이 필요합니다."}, "trend_bad": "상승", "risk_scenario": "소화 불량 및 컨디션 난조 지속으로 인한 업무 효율 저하 리스크."},
    "r-GTP(감마-GTP)": {"label": "r-GTP (알코올)", "safe_high": 63, "warn_high": 100, "advice": {"안전": "담도계 이상이 없으며 간 기능이 안정적입니다.", "경계": "잦은 음주로 간 기능이 과부화된 상태입니다. 금주와 휴식이 필요합니다.", "위험": "알코올성 간 손상 혹은 담도 폐쇄성 질환 가능성이 큽니다."}, "trend_bad": "상승", "risk_scenario": "해독 능력 저하로 인한 무기력증 및 선내 업무 태만 리스크."},
    "T.Cholesterol(총콜레스테롤)": {"label": "T.Cholesterol (콜레스테롤)", "safe_high": 199, "warn_high": 239, "advice": {"안전": "혈관 벽 건강이 양호하며 심혈관 리스크가 낮습니다.", "경계": "이상지질혈증 경계 단계입니다. 식이섬유 섭취를 늘리십시오.", "위험": "동맥경화 및 심근경색 발생 확률이 높습니다. 매우 주의가 필요합니다."}, "trend_bad": "상승", "risk_scenario": "외해 항해 중 급성 심근경색 발생 시 의료 지원 불능으로 인한 사망 위험."},
    "Hemoglobin(혈색소)": {"label": "Hemoglobin (혈색소)", "safe_low": 13, "safe_high": 17, "warn_low": 11, "warn_high": 18, "advice": {"안전": "체내 산소 공급 능력이 우수하며 빈혈 징후가 없습니다.", "경계": "경미한 빈혈 혹은 수분 부족이 의심됩니다. 철분 섭취를 권장합니다.", "위험": "중증 빈혈 상태로 어지럼증과 숨가쁨 증상이 나타날 수 있습니다."}, "trend_bad": "하락", "risk_scenario": "기립성 저혈압으로 인한 실족 및 추락, 작업 중 평형감각 저하 사고."},
    "W.B.C(백혈구수)": {"label": "W.B.C (백혈구)", "safe_high": 10, "warn_high": 12, "advice": {"안전": "면역 체계가 안정적이며 염증 반응이 관찰되지 않습니다.", "경계": "가벼운 염증이나 스트레스로 면역 수치가 불안정한 상태입니다.", "위험": "급성 염증이나 감염이 진행 중입니다. 발열 여부 확인이 필요합니다."}, "trend_bad": "상승", "risk_scenario": "선내 집단 감염병 발생 시 전파 원인 및 본인 합병증 위험."}
}

def load_data_from_google_sheet(name):
    sheet_url = "https://docs.google.com/spreadsheets/d/1EOpOWv83_7Bfkhzw1o78OlVYhdLAEAh5KbFdmtsyl6E/export?format=xlsx"
    try:
        xls = pd.ExcelFile(sheet_url)
        target_sheet = next((s for s in xls.sheet_names if name.replace(" ", "") in s.replace(" ", "")), None)
        if not target_sheet: return None
        raw = pd.read_excel(xls, sheet_name=target_sheet, header=None)
        df = pd.read_excel(xls, sheet_name=target_sheet, skiprows=2)
        years_list = raw.iloc[0, 2:8].dropna().astype(str).str.replace("년", "").tolist()
        doc_note = None
        mask = raw.astype(str).apply(lambda x: x.str.contains('의사소견|진단서|소견', na=False))
        found = np.where(mask)
        if len(found[0]) > 0:
            r, c = found[0][0], found[1][0]
            note_row = raw.iloc[r, c+1:].dropna()
            if not note_row.empty: doc_note = str(note_row.iloc[0])
        res_data = {}
        for key in CRITERIA_MAP.keys():
            search_key = key.split('(')[0]
            row = df[df.iloc[:, 1].astype(str).str.contains(search_key, na=False, case=False)]
            if not row.empty:
                vals = pd.to_numeric(row.iloc[0, 2:2+len(years_list)], errors='coerce').fillna(0).tolist()
                res_data[key] = {"values": vals}
        return {"years": years_list, "data": res_data, "doc_note": doc_note, "sheet_name": target_sheet}
    except: return None

# 3. 사이드바 구성
with st.sidebar:
    st.header("📋 AI 선원 건강 관리")
    search_name = st.text_input("분석 성명", placeholder="성명을 입력하세요")
    search_clicked = st.button("데이터 분석 실행", use_container_width=True)
    
    # 분석 상태 유지
    if search_clicked and search_name:
        st.session_state.current_res = load_data_from_google_sheet(search_name)
        st.session_state.page_view = "result"
    
    st.divider()
    if st.button("🏠 처음 화면으로", use_container_width=True):
        st.session_state.page_view = "welcome"
        st.session_state.current_res = None
        st.rerun()

    st.write("📂 **데이터 원본 관리**")
    sheet_edit_url = "https://docs.google.com/spreadsheets/d/1EOpOWv83_7Bfkhzw1o78OlVYhdLAEAh5KbFdmtsyl6E/edit"
    st.link_button("구글 시트 열기", sheet_edit_url, use_container_width=True)

# 4. 초기 화면 (Welcome Screen) 복구
if "page_view" not in st.session_state or st.session_state.page_view == "welcome":
    st.title("⚓ 선원 보건 안전 AI 리스크 관리 시스템")
    st.info("왼쪽 사이드바에서 성명을 입력하고 [데이터 분석 실행]을 눌러주세요.")
    
    c1, c2, c3 = st.columns(3)
    c1.markdown("#### 📝 데이터 연동\n구글 시트에 기록된 선원들의 다년간 건강검진 데이터를 AI가 즉시 분석합니다.")
    c2.markdown("#### 📈 트렌드 예측\n과거 데이터를 바탕으로 향후 2년 뒤의 건강 지표 리스크를 선제적으로 예측합니다.")
    c3.markdown("#### 🚨 안전 등급\n승선 적합 여부(Fit/Unfit)를 판정하고 긴급 상황 리스크 시나리오를 제공합니다.")
    
    st.image("https://images.unsplash.com/photo-1505228395891-9a51e7e86bf6?ixlib=rb-1.2.1&auto=format&fit=crop&w=1200&q=80", caption="Safe Navigation through AI Health Monitoring")

# 5. 분석 결과 화면
elif st.session_state.page_view == "result":
    res = st.session_state.current_res
    if res:
        st.title(f"⚓ {res['sheet_name']} 님 분석 보고서")
        
        # 데이터 계산
        summary_results = []
        total_score = 100
        years_num = [int(re.sub(r'[^0-9]', '', y)) for y in res['years']]
        clean_years_label = [f"{y}" for y in years_num]
        next_year = max(years_num) + 2 if years_num else 2027

        for key, content in res['data'].items():
            vals = [v for v in content['values'] if v > 0]
            y_list = [years_num[i] for i, v in enumerate(content['values']) if v > 0]
            curr = vals[-1] if vals else 0
            c = CRITERIA_MAP[key]
            
            pred_val = None
            if len(vals) >= 2:
                try: coeffs = np.polyfit(y_list, vals, 1); pred_val = round(coeffs[0] * next_year + coeffs[1], 1)
                except: pass
            
            # 상태 판정
            status, color, loss = "안전", "#28A745", 0
            if key == "Hemoglobin(혈색소)":
                if curr < c['warn_low'] or curr > c['warn_high']: status, color, loss = "위험", "#FF4B4B", 30
                elif curr < c['safe_low'] or curr > c['safe_high']: status, color, loss = "경계", "#FFD700", 7
            else:
                if curr > c['warn_high']: status, color, loss = "위험", "#FF4B4B", 30
                elif curr > c['safe_high']: status, color, loss = "경계", "#FFD700", 7
            
            total_score -= loss
            summary_results.append({"key": key, "val": curr, "status": status, "color": color, "advice": c['advice'][status], "pred": pred_val})

        # 점수 표시
        c1, c2 = st.columns([1, 2])
        final_score = max(0, total_score)
        c1.metric("종합 보건 점수", f"{final_score} / 100")
        with c2:
            if any(r['status'] == "위험" for r in summary_results): st.error("### 최종 판정: 승선 부적합 (Unfit)")
            elif final_score >= 80: st.success("### 최종 판정: 승선 적합 (Fit)")
            else: st.warning("### 최종 판정: 조건부 적합 (Conditional Fit)")
        
        st.divider()

        with st.expander("🧐 상세분석 및 소견 확인하기", expanded=True):
            if res['doc_note']: st.info(f"📋 **진단서 공식 의사소견:** {res['doc_note']}")
            cols = st.columns(2)
            for i, item in enumerate(summary_results):
                with cols[i % 2]:
                    c = CRITERIA_MAP[item['key']]
                    st.markdown(f"""
                    <div style="padding:15px; border-radius:10px; border-left:8px solid {item['color']}; background-color:#fdfdfd; margin-bottom:15px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); color: black;">
                        <b style="font-size:1.1rem;">{c['label']}</b> <br>
                        <span style="color:{item['color']}; font-weight:bold;">상태: {item['status']} ({item['val']})</span><br>
                        <p style="font-size:0.85rem; margin-top:10px; line-height:1.5;">
                            <b>💡 AI 소견:</b> {item['advice']}<br>
                            <b>⚓ 선내 리스크:</b> {c['risk_scenario']}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

        st.divider()

        # 6. [오류 수정] 그래프 지표 선택 및 렌더링
        st.subheader("📈 리스크 추세 및 2년 후 예측")
        
        # 지표 선택 시 흰 화면이 뜨지 않도록 key값 부여 및 세션 유지
        sel_label = st.selectbox("확인 지표 선택", 
                               options=[CRITERIA_MAP[k]['label'] for k in res['data'].keys()],
                               key="indicator_select")
        
        # 선택된 라벨로 키값 찾기
        sel_key = next(k for k, v in CRITERIA_MAP.items() if v['label'] == sel_label)
        c_sel = CRITERIA_MAP[sel_key]
        res_item = next(it for it in summary_results if it["key"] == sel_key)
        
        y_vals = res['data'][sel_key]['values']
        v_clean = [v for v in y_vals if v > 0]
        current_labels = clean_years_label[:len(y_vals)]

        if v_clean:
            st.markdown(f"#### 📊 {c_sel['label']} 추이 ({current_labels[0]}년~{current_labels[-1]}년)")
            
            # 매번 새로운 figure 객체를 생성하여 충돌 방지
            fig, ax = plt.subplots(figsize=(10, 5))
            d_max = max(v_clean + [res_item['pred'] if res_item['pred'] else 0, c_sel['warn_high']]) * 1.4
            
            ax.axhspan(0, c_sel.get('safe_high', 10), color='#4CAF50', alpha=0.1, label='Safe')
            ax.axhspan(c_sel.get('safe_high', 10), c_sel['warn_high'], color='#FFEB3B', alpha=0.15, label='Caution')
            ax.axhspan(c_sel['warn_high'], d_max*2, color='#F44336', alpha=0.1, label='Danger')
            
            ax.plot(current_labels, y_vals, marker='o', color='#000080', lw=3, ms=8, label='Actual')
            
            if res_item['pred'] is not None:
                pred_year = str(next_year)
                ax.plot([current_labels[-1], pred_year], [v_clean[-1], res_item['pred']], color='#B71C1C', lw=3, ls=':', marker='D', ms=8, label='AI Predict')
                ax.text(pred_year, res_item['pred'] + (d_max*0.02), f'{res_item["pred"]}', ha='center', fontweight='bold', color='#B71C1C')

            for i, v in enumerate(y_vals):
                if v > 0: ax.text(i, v + (d_max*0.02), f'{v}', ha='center', fontsize=10, fontweight='bold')

            ax.set_ylim(0, d_max)
            ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
            
            # 렌더링 후 메모리 해제
            st.pyplot(fig)
            plt.close(fig)
            
    else:
        st.error("성명을 찾을 수 없거나 데이터 로드에 실패했습니다.")
        st.session_state.page_view = "welcome"
