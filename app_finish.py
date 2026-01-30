import streamlit as st
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
import pandas as pd
import json
import datetime
import time

# -----------------------------------------------------------------------------
# [보안] Secrets 설정 확인
# -----------------------------------------------------------------------------
try:
    MY_API_KEY = st.secrets["GOOGLE_API_KEY"]
    TEAM_PASSWORD = st.secrets["TEAM_PASSWORD"]
except (KeyError, FileNotFoundError):
    st.error("🚨 서버 설정 오류: Streamlit Secrets 설정을 확인해주세요.")
    st.stop()

# -----------------------------------------------------------------------------
# 페이지 기본 설정 & 로그인 UI
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
            elif pw: st.error("❌ 비밀번호가 틀립니다.")
    return False

if not check_password(): st.stop()

# -----------------------------------------------------------------------------
# [Backend] 에러 방지용 전략 생성 엔진
# -----------------------------------------------------------------------------
def generate_senior_strategy(api_key, p_name, p_target, p_details, platform, tone):
    genai.configure(api_key=api_key)
    
    # [404 해결] 사용 가능한 모델 자동 감지 로직
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in models else models[0]
    except: 
        model_name = 'models/gemini-pro'

    model = genai.GenerativeModel(model_name)
    
    prompt = f"""
    당신은 대한민국 최고의 시니어 퍼포먼스 마케터입니다. {p_name} 제품에 대해 {platform} 매체에 최적화된 전략을 수립하세요.

    [지침]
    1. 가독성을 위해 반드시 '문단 나눔'을 적용하여 상세히 서술하세요.
    2. 뇌피셜이 아닌 타겟의 심리와 라이프스타일을 기반으로 CEP를 도출하세요.
    
    [출력 형식] 반드시 아래 JSON 배열로만 답변하세요:
    [
      {{
        "id": 1,
        "concept": "전략 핵심 컨셉",
        "situation": "구체적인 상황 묘사 (문단 나눔 필수)",
        "pain_point": "고객의 숨은 결핍 분석",
        "hooking_copy": "매체 최적화 후킹 카피",
        "visual_guide": "비주얼 및 연출 가이드 (상세 서술)",
        "expected_effect": "기대 효과 및 KPI"
      }}
    ]
    """

    # [429 해결] 재시도 로직 강화
    for attempt in range(3):
        try:
            response = model.generate_content(prompt, generation_config=GenerationConfig(temperature=0.75))
            return response.text
        except Exception as e:
            if "429" in str(e):
                time.sleep(12 * (attempt + 1))
                continue
            return f"Error: {str(e)}"
    return "Error: Quota exceeded"

# -----------------------------------------------------------------------------
# [Frontend] 레이아웃 및 디자인
# -----------------------------------------------------------------------------
st.title("🧠 CEP 퍼포먼스 마케팅 솔루션")
st.markdown("---")

# 좌우 배치: 입력(좌) / 결과(우)
col_input, col_result = st.columns([1, 1.4])

with col_input:
    st.subheader("📦 기획 데이터 입력")
    with st.sidebar:
        st.header("🎛️ 옵션 설정")
        platform = st.radio("노출 매체", ["SNS 숏폼", "SNS 피드", "GFA/배너", "검색광고"], index=1)
        tone = st.select_slider("카피 톤앤매너", options=["순한맛", "논리적", "매운맛"], value="매운맛")

    with st.container(border=True):
        p_name = st.text_input("제품/서비스명", placeholder="예: 고기어트 간편식")
        p_target = st.text_input("🎯 핵심 타겟", placeholder="예: 30대 직장인 남성")
        p_details = st.text_area("🔧 제품 핵심 특장점", height=250, placeholder="특징들을 상세히 적어주세요.")
        generate_btn = st.button("🚀 시니어 전략 도출하기", use_container_width=True, type="primary")

with col_result:
    st.subheader("📊 전략 리포트 분석 결과")
    if generate_btn:
        if not p_name or not p_target:
            st.warning("⚠️ 제품명과 타겟 정보를 입력해주세요.")
        else:
            with st.spinner("시니어 마케터가 전략을 수립 중입니다..."):
                # [NameError 수정 완료]
                raw_text = generate_senior_strategy(MY_API_KEY, p_name, p_target, p_details, platform, tone)
                
                if "Error" in raw_text:
                    st.error("❌ 현재 요청량이 많아 처리가 지연되고 있습니다. 잠시 후 다시 시도해 주세요.")
                else:
                    try:
                        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
                        strategies = json.loads(clean_json)
                        
                        st.success(f"✅ 전문 마케팅 전략이 도출되었습니다.")
                        
                        # [UI 강화] 카드형 레이아웃 및 탭 시스템
                        for s in strategies:
                            with st.container(border=True):
                                st.markdown(f"### 📍 전략 {s['id']}: {s['concept']}")
                                
                                # 탭으로 기획 로직과 비주얼 가이드를 깔끔하게 분리
                                tab_logic, tab_visual = st.tabs(["📝 기획 로직 분석", "🎬 제작 가이드라인"])
                                
                                with tab_logic:
                                    st.markdown("**🔍 상세 상황 및 CEP 분석**")
                                    st.write(s['situation']) # 문단 나눔 유지
                                    st.markdown(f"**💡 핵심 페인포인트:** {s['pain_point']}")
                                    
                                with tab_visual:
                                    st.error(f"**⚡ 메인 후킹 카피:** {s['hooking_copy']}")
                                    st.info(f"**📸 연출 가이드:**\n\n{s['visual_guide']}")
                                    st.success(f"**📈 기대 효과:** {s['expected_effect']}")
                                
                                st.markdown("<br>", unsafe_allow_html=True)
                                
                    except:
                        st.error("해석 중 오류 발생. 다시 시도해 주세요.")
                        st.text(raw_text)
