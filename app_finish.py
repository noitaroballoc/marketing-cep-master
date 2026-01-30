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
    st.error("🚨 서버 설정 오류: Secrets에 API 키와 비밀번호가 설정되지 않았습니다.")
    st.stop()

# -----------------------------------------------------------------------------
# 페이지 기본 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="CEP 퍼포먼스 마케팅 솔루션",
    page_icon="🧠",
    layout="wide"
)

# -----------------------------------------------------------------------------
# [로그인 기능] (디자인 유지)
# -----------------------------------------------------------------------------
def check_password():
    def password_entered():
        if st.session_state["password"] == TEAM_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
        st.markdown("<br>" * 10, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            with st.container(border=True):
                st.markdown("<h2 style='text-align: center;'>🔒 Team Access</h2>", unsafe_allow_html=True)
                st.caption("팀 전용 접속 코드를 입력하세요.")
                st.text_input(
                    label="Password", type="password", on_change=password_entered, 
                    key="password", label_visibility="collapsed", placeholder="비밀번호 입력"
                )
                if "password_correct" in st.session_state and not st.session_state["password_correct"]:
                    st.error("🚫 비밀번호가 일치하지 않습니다.")
        return False
    return True

if not check_password():
    st.stop()

# -----------------------------------------------------------------------------
# 세션 상태 초기화 및 팝업
# -----------------------------------------------------------------------------
if 'history' not in st.session_state:
    st.session_state.history = []

@st.dialog("💡 시니어 마케터 가이드")
def show_cep_guide():
    st.markdown("""
        ### 1️⃣ 시니어 마케팅 사고 (Senior Logic)
        단순 카피 생성이 아닙니다. 타겟의 결핍(Pain Point)과 구매 동기를 분석하여 전략적 가설을 수립합니다.
        ### 2️⃣ 데이터 기반 분석 (Fact Based)
        웹 검색을 통해 수집된 실제 고객 반응과 경쟁사 데이터를 바탕으로 전략을 짭니다.
        ### 3️⃣ 매체 최적화 가이드
        각 매체 특성에 맞는 비주얼 가이드와 예상 KPI를 함께 제공합니다.
    """)
    if st.button("전략 수립 시작하기 🚀", type="primary"):
        st.rerun()

if 'cep_popup_shown' not in st.session_state:
    show_cep_guide()
    st.session_state.cep_popup_shown = True

# -----------------------------------------------------------------------------
# 사이드바 설정 (디자인 유지)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("🎛️ 마케팅 옵션 설정")
    st.success("✅ Senior Master Logic 활성화")
    st.markdown("---")
    platform = st.radio(
        "광고 매체 선택",
        ["SNS 숏폼 (릴스/틱톡)", "SNS 피드 (인스타/페북)", "GFA/배너 (네이버/카카오)", "검색광고 (TDA)"],
        index=1
    )
    tone = st.select_slider(
        "카피 강도 설정",
        options=["순한맛 (공감)", "논리적 (팩트)", "매운맛 (손실회피)"],
        value="매운맛 (손실회피)"
    )
    st.caption("Developed for Professional Marketers")

# -----------------------------------------------------------------------------
# 메인 화면 구성
# -----------------------------------------------------------------------------
st.title("🧠 시니어 CEP 퍼포먼스 전략 솔루션")
st.info("💡 **시니어 전략 모델:** 단순 카피가 아닌 '상황(CEP) - 동기 - 해결논리' 체계로 분석합니다.")
st.divider()

tab1, tab2 = st.tabs(["⚡ 전략 생성", "🗂️ 저장된 기록"])

with tab1:
    col_in, col_out = st.columns([1, 1.2])

    with col_in:
        st.subheader("📦 기획 데이터 입력")
        with st.container(border=True):
            p_name = st.text_input("제품/서비스명", placeholder="예: 고기어트 다이어트 도시락")
            p_target = st.text_input("🎯 핵심 타겟 세그먼트", placeholder="예: 야근이 잦고 배달음식에 지친 30대 직장인")
            p_details = st.text_area("🔧 제품 핵심 특장점", height=200, placeholder="저칼로리, 실온보관, 고단백 등 상세 내용을 적어주세요.")
            generate_btn = st.button("🚀 시니어 전략 리포트 도출", use_container_width=True, type="primary")

    with col_out:
        st.subheader("📊 전략 리포트 분석 결과")
        result_area = st.container()

# -----------------------------------------------------------------------------
# [Back-end] 시니어 마케팅 엔진
# -----------------------------------------------------------------------------
def get_safe_model(api_key):
    genai.configure(api_key=api_key)
    try:
        # 사용 가능한 모델 중 flash 모델을 우선 검색 (404 방지)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m in models:
            if '1.5-flash' in m: return m
        return models[0]
    except: return 'gemini-pro'

def generate_senior_strategy(api_key, name, target, details, platform, tone):
    # 1. 실시간 웹 검색 (Fact 수집)
    try:
        with DDGS() as ddgs:
            search_res = list(ddgs.text(f"{name} 실제 고객 후기 단점", max_results=2))
            context = "\n".join([r['body'][:250] for r in search_res])
    except: context = "검색 데이터 없음"

    # 2. 모델 설정 및 시니어 프롬프트 주입
    model_name = get_safe_model(api_key)
    model = genai.GenerativeModel(model_name)
    
    prompt = f"""
    당신은 10년차 시니어 퍼포먼스 마케터입니다. {name} 제품에 대해 {platform} 매체에 최적화된 전략을 수립하세요.
    [데이터]: {context} / [타겟]: {target} / [제품특징]: {details} / [톤]: {tone}

    [사고 단계]
    1. 상황(CEP): 고객이 우리 제품을 떠올리는 결정적 순간 정의.
    2. 페인포인트: 타겟이 느끼는 가장 큰 심리적/기능적 결핍.
    3. 후킹 논리: 제품 특징을 어떻게 해결책으로 제시할 것인가?
    
    [결과 형식] 반드시 아래 JSON 배열만 출력하세요. 다른 말은 금지합니다.
    [
      {{
        "title": "전략 컨셉 명칭",
        "situation": "구체적인 라이프스타일 상황",
        "logic": "제품 소구점 연결 논리",
        "main_copy": "매체 최적화 후킹 카피",
        "visual": "디자이너를 위한 비주얼 가이드",
        "kpi": "예상 개선 지표"
      }}
    ]
    """

    for attempt in range(3):
        try:
            response = model.generate_content(prompt, generation_config=GenerationConfig(temperature=0.75))
            return response.text
        except Exception as e:
            if "429" in str(e):
                time.sleep(15 * (attempt + 1))
                continue
            return f"Error: {str(e)}"
    return "Error: 할당량 소진"

# -----------------------------------------------------------------------------
# 실행 및 UI 렌더링
# -----------------------------------------------------------------------------
if generate_btn:
    if not p_name or not p_target:
        st.warning("⚠️ 제품명과 타겟 정보는 필수입니다.")
    else:
        with col_out:
            with st.spinner("시니어 마케터가 가설을 수립하고 있습니다..."):
                raw_text = generate_senior_strategy(MY_API_KEY, p_name, p_target, p_details, platform, tone)
                
                if "Error" in raw_text:
                    st.error(raw_text)
                else:
                    try:
                        # JSON 파싱 및 UI 가공
                        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
                        strategies = json.loads(clean_json)
                        
                        st.success(f"✅ 전략 수립 완료!")
                        
                        for i, s in enumerate(strategies):
                            with st.container(border=True):
                                st.markdown(f"#### 📍 전략 {i+1}: {s['title']}")
                                st.write(f"**🕵️ 상황 분석:** {s['situation']}")
                                st.write(f"**🧠 소구 논리:** {s['logic']}")
                                st.divider()
                                st.error(f"**⚡ 메인 카피:** {s['main_copy']}")
                                st.info(f"**🎨 비주얼 가이드:** {s['visual']}")
                                st.caption(f"📈 기대 효과: {s['kpi']}")
                        
                        # 히스토리 저장
                        st.session_state.history.insert(0, {"timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "product": p_name, "data": strategies})
                    except:
                        st.error("해석 중 오류 발생")
                        st.text(raw_text)

with tab2:
    for h in st.session_state.history:
        with st.expander(f"🕒 {h['timestamp']} - {h['product']}"):
            st.write(h['data'])
