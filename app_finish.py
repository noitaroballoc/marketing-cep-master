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
# 페이지 기본 설정 (기존 UI 유지)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="CEP 퍼포먼스 마케팅 솔루션", page_icon="🧠", layout="wide")

# [로그인 기능 - 기존 UI 100% 동일]
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
                st.text_input(label="Password", type="password", on_change=password_entered, key="password", label_visibility="collapsed", placeholder="비밀번호 입력")
                if "password_correct" in st.session_state and not st.session_state["password_correct"]:
                    st.error("🚫 비밀번호가 일치하지 않습니다.")
        return False
    return True

if not check_password(): st.stop()

# [기존 세션 및 사이드바 UI 유지]
if 'history' not in st.session_state: st.session_state.history = []

with st.sidebar:
    st.header("🎛️ 마케팅 옵션 설정")
    platform = st.radio("매체", ["SNS 숏폼 (릴스/틱톡)", "SNS 피드 (인스타/페북)", "GFA/배너 (네이버/카카오)", "검색광고 (TDA)"], index=2)
    tone = st.select_slider("톤앤매너", options=["순한맛 (공감/위로)", "논리적 (기능/정보)", "매운맛 (공포/팩폭)"], value="매운맛 (공포/팩폭)")

# -----------------------------------------------------------------------------
# [핵심 로직] 404 및 429 방어형 함수
# -----------------------------------------------------------------------------
def get_working_model(api_key):
    """실시간으로 사용 가능한 모델명을 조회하여 404 에러를 방지합니다."""
    genai.configure(api_key=api_key)
    try:
        # 지원되는 모델 목록을 가져와서 flash나 pro가 포함된 이름을 찾음
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini-1.5-flash' in m.name: return m.name
        # 만약 1.5-flash가 없으면 가장 기본인 gemini-pro 반환
        return 'models/gemini-pro'
    except:
        return 'models/gemini-pro'

def generate_strategy(api_key, name, target, details, platform, tone):
    # 검색 데이터 수집
    try:
        with DDGS() as ddgs:
            search_res = list(ddgs.text(f"{name} 실제 후기", max_results=2))
            context = "\n".join([f"정보: {r['body'][:200]}" for r in search_res])
    except:
        context = "검색 데이터를 불러오지 못했습니다."

    # 404 방어: 안전한 모델 이름 가져오기
    target_model_name = get_working_model(api_key)
    model = genai.GenerativeModel(target_model_name)
    
    prompt = f"제품:{name}, 타겟:{target}, 매체:{platform}, 톤:{tone}\n데이터:{context}\n마케팅 CEP 7가지를 JSON 배열로만 작성해."

    # 429 방어: 지수 백오프 재시도 로직
    for attempt in range(3):
        try:
            response = model.generate_content(prompt, generation_config=GenerationConfig(temperature=0.7))
            return response.text
        except Exception as e:
            if "429" in str(e):
                wait_time = (attempt + 1) * 12 # 12초, 24초... 대기
                st.warning(f"⚠️ 요청이 많아 {wait_time}초 후 다시 시도합니다...")
                time.sleep(wait_time)
                continue
            return f"Error: {str(e)}"
    return "🚨 할당량이 모두 소진되었습니다. 잠시 후 시도해주세요."

# -----------------------------------------------------------------------------
# [UI 출력 부분 - 기존과 동일]
# -----------------------------------------------------------------------------
st.title("🧠 CEP 퍼포먼스 마케팅 솔루션")
col1, col2 = st.columns([1, 1])
with col1:
    p_name = st.text_input("제품명")
    p_target = st.text_input("타겟")
    p_details = st.text_area("제품 특징", height=200)
    generate_btn = st.button("🚀 전략 도출하기", type="primary", use_container_width=True)

if generate_btn:
    with col2:
        with st.spinner("분석 중..."):
            raw_text = generate_strategy(MY_API_KEY, p_name, p_target, p_details, platform, tone)
            if "Error" in raw_text or "🚨" in raw_text:
                st.error(raw_text)
            else:
                try:
                    # JSON 파싱 및 결과 출력 로직 (기존과 동일)
                    json_str = raw_text.replace("```json", "").replace("```", "").strip()
                    data = json.loads(json_str)
                    for item in data:
                        with st.expander(f"📌 {item.get('cep_title')}", expanded=True):
                            st.write(item.get('hooking_copy'))
                except:
                    st.error("결과 해석 중 오류가 발생했습니다.")
                    st.text(raw_text)
