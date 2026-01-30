import streamlit as st
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
import pandas as pd
import json
import datetime
import time
from duckduckgo_search import DDGS 

# -----------------------------------------------------------------------------
# [보안] 비밀번호 & API 키 설정
# -----------------------------------------------------------------------------
try:
    MY_API_KEY = st.secrets["GOOGLE_API_KEY"]
    TEAM_PASSWORD = st.secrets["TEAM_PASSWORD"]
except (KeyError, FileNotFoundError):
    st.error("🚨 서버 설정 오류: Secrets 설정을 확인해주세요.")
    st.stop()

# -----------------------------------------------------------------------------
# 페이지 기본 설정
# -----------------------------------------------------------------------------
st.set_page_config(page_title="CEP 퍼포먼스 마케팅 솔루션", page_icon="🧠", layout="wide")

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]: return True
    st.markdown("<br>" * 10, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center;'>🔒 Team Access</h3>", unsafe_allow_html=True)
            pw = st.text_input("접속 코드를 입력하세요", type="password", label_visibility="collapsed")
            if pw == TEAM_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
    return False

if not check_password(): st.stop()

# -----------------------------------------------------------------------------
# [Back-end] 시니어 전략 엔진 (가독성 최적화 버전)
# -----------------------------------------------------------------------------
def generate_senior_strategy(api_key, name, target, details, platform, tone):
    genai.configure(api_key=api_key)
    
    # [404 해결] 사용 가능한 모델 자동 조회
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in models else models[0]
    except: model_name = 'gemini-pro'

    model = genai.GenerativeModel(model_name)
    
    # 전략 개수 강제 조항을 제거하여 할당량 소모 최적화
    prompt = f"""
    당신은 10년차 시니어 퍼포먼스 마케터입니다. {name} 제품에 대해 {platform} 매체에 최적화된 전략 가설을 수립하세요.

    [입력 데이터]
    - 제품명: {name} / 타겟: {target}
    - 상세특징: {details} / 톤앤매너: {tone}

    [작성 가이드라인]
    1. **문단 나눔**: 모든 설명은 가독성을 위해 적절한 문단 나눔을 적용하세요.
    2. **전문성**: 상황(CEP), 고객 심리, 매체 특성을 시니어 관점에서 세밀하게 분석하세요.
    3. **비주얼 가이드**: 디자이너가 바로 작업할 수 있도록 장면을 구체적으로 묘사하세요.

    [결과 형식] 반드시 아래 구조의 JSON 배열로만 답변하세요.
    [
      {{
        "id": 1,
        "concept": "전략 핵심 컨셉",
        "situation": "구체적인 상황 묘사 (문단 나눔 적용)",
        "pain_point": "고객의 숨은 결핍 분석",
        "hooking_copy": "매체 최적화 후킹 카피",
        "visual_guide": "비주얼 연출 가이드 (상세 서술)",
        "expected_effect": "예상되는 KPI 및 기대 효과"
      }}
    ]
    """

    # [429 해결] 재시도 로직
    for attempt in range(3):
        try:
            response = model.generate_content(prompt, generation_config=GenerationConfig(temperature=0.75))
            return response.text
        except Exception as e:
            if "429" in str(e):
                time.sleep(10 * (attempt + 1))
                continue
            return f"Error: {str(e)}"
    return "Error: 할당량 소진"

# -----------------------------------------------------------------------------
# [Front-end] 메인 UI 디자인 (기존 레이아웃 유지)
# -----------------------------------------------------------------------------
st.title("🧠 CEP 퍼포먼스 마케팅 솔루션")
st.markdown("---")

col_in, col_out = st.columns([1, 1.3])

with col_in:
    st.subheader("📦 기획 데이터 입력")
    with st.container(border=True):
        p_name = st.text_input("제품/서비스명", placeholder="예: 고기어트 돼지고기 간편식")
        p_target = st.text_input("🎯 핵심 타겟", placeholder="예: 식단이 지겨운 30대 남성 직장인")
        p_details = st.text_area("🔧 제품 핵심 특장점", height=250, placeholder="상세한 특징을 적을수록 전략이 날카로워집니다.")
        generate_btn = st.button("🚀 시니어 전략 도출하기", use_container_width=True, type="primary")

with col_out:
    st.subheader("📊 전략 리포트 분석 결과")
    if generate_btn:
        with st.spinner("전략 가설을 수립 중입니다..."):
            raw_text = generate_senior_strategy(MY_API_KEY, p_name, p_target, p_details, platform, tone)
            
            if "Error" in raw_text:
                st.error("❌ 현재 API 사용량이 많습니다. 잠시 후 다시 시도해주세요.")
            else:
                try:
                    clean_json = raw_text.replace("```json", "").replace("```", "").strip()
                    strategies = json.loads(clean_json)
                    
                    st.success(f"✅ 전문 마케팅 전략이 도출되었습니다.")
                    
                    for s in strategies:
                        # [UI 가독성 강화] 카드 및 탭 구조
                        with st.container(border=True):
                            st.markdown(f"### 📍 전략 {s['id']}: {s['concept']}")
                            
                            tab_a, tab_b = st.tabs(["📝 기획 로직", "🎨 비주얼 가이드"])
                            
                            with tab_a:
                                st.markdown("**🔍 시장 상황 및 CEP 분석**")
                                st.write(s['situation'])
                                st.markdown(f"**💡 타겟 페인포인트:** {s['pain_point']}")
                                
                            with tab_b:
                                st.error(f"**⚡ 메인 카피:** {s['hooking_copy']}")
                                st.info(f"**📸 연출 가이드:** \n\n{s['visual_guide']}")
                                st.success(f"**📈 기대 효과:** {s['expected_effect']}")
                            
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                except:
                    st.error("데이터 처리 중 오류가 발생했습니다. 다시 시도해주세요.")
                    st.text(raw_text)
