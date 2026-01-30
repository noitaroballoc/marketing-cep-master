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
    st.error("🚨 서버 설정 오류: Streamlit Secrets에 API 키와 비밀번호가 설정되지 않았습니다.")
    st.stop()

# -----------------------------------------------------------------------------
# 페이지 기본 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="CEP 퍼포먼스 마케팅 솔루션",
    page_icon="🌐",
    layout="wide"
)

# -----------------------------------------------------------------------------
# [로그인 기능]
# -----------------------------------------------------------------------------
def check_password():
    def password_entered():
        if st.session_state["password"] == TEAM_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
        st.markdown("<br>" * 12, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            with st.container(border=True):
                st.markdown("<h2 style='text-align: center;'>🔒 Team Access</h2>", unsafe_allow_html=True)
                st.caption("접속 코드를 입력하세요.")
                st.text_input(label="Password", type="password", on_change=password_entered, key="password", label_visibility="collapsed", placeholder="비밀번호 입력")
                if "password_correct" in st.session_state and not st.session_state["password_correct"]:
                    st.error("🚫 비밀번호가 일치하지 않습니다.")
        st.markdown("<br>" * 15, unsafe_allow_html=True)
        return False
    else:
        return True

if not check_password():
    st.stop()

# =============================================================================
# 메인 앱 기능 함수
# =============================================================================

@st.dialog("💡 프로그램 설명")
def show_cep_guide():
    st.markdown(
        """
        ### 1️⃣ 직접 검색 기반 분석 (Search Agent)
        이 프로그램은 실제 웹 검색을 수행하여 데이터를 수집한 뒤 분석합니다.
        ### 2️⃣ 무엇을 얻을 수 있나요?
        팩트(Fact)에 기반한 경쟁 우위 전략과 CEP를 도출합니다.
        """
    )
    if st.button("전략 짜러가기! 🚀", type="primary"):
        st.rerun()

if 'cep_popup_shown' not in st.session_state:
    show_cep_guide()
    st.session_state.cep_popup_shown = True

if 'history' not in st.session_state:
    st.session_state.history = []

# -----------------------------------------------------------------------------
# [핵심] API 및 모델 관리 로직
# -----------------------------------------------------------------------------
def get_best_available_model(api_key):
    """할당량이 넉넉한 Flash 모델을 최우선으로 선택합니다."""
    genai.configure(api_key=api_key)
    try:
        all_models = list(genai.list_models())
        text_models = [m.name for m in all_models if 'generateContent' in m.supported_generation_methods]
        
        # 할당량 이슈가 적은 Flash 모델을 1, 2순위로 배치
        priority_keywords = ['gemini-1.5-flash', 'gemini-2.0-flash', 'gemini-1.5-pro']
        
        for kw in priority_keywords:
            for m in text_models:
                if kw in m:
                    return m
        return text_models[0] if text_models else None
    except:
        return None

def perform_web_search(query, max_results=3):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, region='kr-kr', safesearch='off', max_results=max_results))
            search_summary = ""
            for idx, res in enumerate(results):
                search_summary += f"[{idx+1}] 제목: {res['title']}\n내용: {res['body']}\n\n"
            return search_summary if search_summary else "검색 결과 없음"
    except Exception as e:
        return f"검색 중 오류 발생: {str(e)}"

def check_compliance_risks(text):
    risky_words = ["최고", "100%", "완치", "무조건", "보장", "부작용 없", "즉시", "유일", "최초"]
    found = [word for word in risky_words if word in text]
    return found

def extract_json_from_text(text):
    try:
        start_idx = text.find('[')
        end_idx = text.rfind(']')
        if start_idx != -1 and end_idx != -1:
            return json.loads(text[start_idx : end_idx + 1])
        return json.loads(text.replace("```json", "").replace("```", "").strip())
    except:
        raise Exception("JSON 파싱 실패")

def generate_strategy(api_key, name, target, details, platform, tone):
    # 1. 검색 데이터 수집
    search_result = perform_web_search(f"{name} 실제 후기 장단점")
    
    # 2. 모델 설정 및 재시도 로직
    active_model_name = get_best_available_model(api_key)
    if not active_model_name:
        return "Error: 모델을 찾을 수 없습니다."

    model = genai.GenerativeModel(active_model_name)
    
    prompt = f"""
    당신은 대한민국 최고의 퍼포먼스 마케터입니다. 아래 정보를 바탕으로 CEP 전략 7가지를 JSON 형식으로만 출력하세요.
    제품명: {name}, 타겟: {target}, 매체: {platform}, 톤: {tone}
    검색데이터: {search_result}
    상세설명: {details}
    
    출력 형식은 반드시 [{{"cep_title": "...", "situation_summary": "...", "thought": "...", "trigger_behavior": "...", "concept_keyword": "...", "ref_keyword": "...", "hooking_copy": "...", "visual_guide": "...", "landing_section": "..."}}] 형태여야 합니다.
    """

    # 429 에러 대응 재시도 루프
    for attempt in range(3):
        try:
            response = model.generate_content(prompt, generation_config=GenerationConfig(temperature=0.7))
            return response.text
        except Exception as e:
            if "429" in str(e):
                time.sleep(10 * (attempt + 1)) # 점진적으로 대기 시간 증가
                continue
            return f"Error: {str(e)}"
    return "Error: 할당량 초과로 인해 처리에 실패했습니다. 잠시 후 다시 시도해주세요."

# -----------------------------------------------------------------------------
# UI 레이아웃
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("🎛️ 마케팅 옵션 설정")
    platform = st.radio("매체", ["SNS 숏폼", "SNS 피드", "GFA/배너", "검색광고"], index=2)
    tone = st.select_slider("톤", options=["순한맛", "논리적", "매운맛"], value="매운맛")

st.title("🌐 CEP 퍼포먼스 마케팅 솔루션")
tab1, tab2 = st.tabs(["⚡ 전략 생성", "🗂️ 저장된 기록"])

with tab1:
    col1, col2 = st.columns([1, 1])
    with col1:
        product_name = st.text_input("제품명", placeholder="예: 다이어트학교 리압스텝퍼")
        target_audience = st.text_input("타겟", placeholder="예: 4050 주부")
        product_details = st.text_area("제품 특징", height=150)
        generate_btn = st.button("🚀 전략 도출하기", use_container_width=True, type="primary")

    with col2:
        if generate_btn:
            if not product_name or not target_audience:
                st.warning("정보를 입력해주세요.")
            else:
                with st.spinner("AI가 전략을 짜고 있습니다... (약 10~30초)"):
                    raw_text = generate_strategy(MY_API_KEY, product_name, target_audience, product_details, platform, tone)
                    
                    if "Error" in raw_text:
                        st.error(raw_text)
                    else:
                        try:
                            data = extract_json_from_text(raw_text)
                            st.session_state.history.insert(0, {"timestamp": datetime.datetime.now().strftime("%H:%M:%S"), "product": product_name, "data": data})
                            for item in data:
                                with st.expander(f"📌 {item['cep_title']}", expanded=True):
                                    st.write(f"**상황:** {item['situation_summary']}")
                                    st.error(f"**후킹 카피:** {item['hooking_copy']}")
                                    st.caption(f"비주얼 가이드: {item['visual_guide']}")
                        except:
                            st.error("결과 해석 중 오류가 발생했습니다. 다시 시도해 주세요.")
                            st.text(raw_text)

with tab2:
    for h in st.session_state.history:
        st.write(f"🕒 {h['timestamp']} - {h['product']}")
        st.json(h['data'])
