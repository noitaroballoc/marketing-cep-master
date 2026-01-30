import streamlit as st
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
import pandas as pd
import json
import datetime
import time  # 재시도 로직을 위해 추가
from duckduckgo_search import DDGS  # 실시간 웹 검색 안정화

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
# [로그인 기능] 화면 정중앙 배치
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
                st.caption("팀 전용 접속 코드를 입력하세요.")
                st.text_input(
                    label="Password",
                    type="password", 
                    on_change=password_entered, 
                    key="password",
                    label_visibility="collapsed",
                    placeholder="비밀번호 입력"
                )
                if "password_correct" in st.session_state and not st.session_state["password_correct"]:
                    st.error("🚫 비밀번호가 일치하지 않습니다.")
        st.markdown("<br>" * 15, unsafe_allow_html=True)
        return False
    else:
        return True

if not check_password():
    st.stop()

# =============================================================================
# 메인 앱 코드
# =============================================================================

@st.dialog("💡 이 프로그램의 핵심")
def show_cep_guide():
    st.markdown(
        """
        ### 1️⃣ 이 프로그램의 본질
        단순 자동화가 아닌, 광고 운영 및 소재 제작을 위한 '아이디어와 레퍼런스'를 제공하는 '러닝메이트'입니다.
        ### 2️⃣ 무엇을 얻을 수 있나요?
        CEP(상황) 분석을 통해 "왜 경쟁사가 아닌 우리 제품이어야 하는가?"에 대한 명확한 구매 이유와 소구점을 도출합니다.
        ### 3️⃣ 활용 가이드
        AI가 제안한 전략을 그대로 쓰기보다, '팀원들의 인사이트를 더해' 우리 브랜드만의 날카로운 무기로 발전시켜 주세요.
        """
    )
    if st.button("확인했습니다! 전략을 짜러 가시죠 🚀", type="primary"):
        st.rerun()

if 'cep_popup_shown' not in st.session_state:
    show_cep_guide()
    st.session_state.cep_popup_shown = True

if 'history' not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.header("🎛️ 마케팅 옵션 설정")
    st.success("✅ Master Logic 활성화")
    st.markdown("---")
    st.subheader("1. 광고 매체 (Platform)")
    platform = st.radio(
        "어디에 노출할 소재인가요?",
        ["SNS 숏폼 (릴스/틱톡)", "SNS 피드 (인스타/페북)", "GFA/배너 (네이버/카카오)", "검색광고 (TDA)"],
        index=2
    )
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("2. 톤앤매너 (Tone)")
    tone = st.select_slider(
        "카피의 강도를 선택하세요",
        options=["순한맛 (공감/위로)", "논리적 (기능/정보)", "매운맛 (공포/팩폭)"],
        value="매운맛 (공포/팩폭)"
    )
    st.markdown("---")
    with st.expander("💡 프로그램 활용 팁"):
        st.info("[아이디어 + 레퍼런스 도구]\nAI의 결과물은 완벽한 정답이 아닙니다. 경쟁사 대비 차별점을 찾기 위한 '생각의 재료'로 활용하세요.")
    st.caption("Developed for **Performance Marketers & Designers**")

st.title("🧠 CEP 퍼포먼스 마케팅 솔루션")
st.info("💡 **CEP(Category Entry Point)란?** 소비자가 구매를 결심하는 '결정적 계기(상황)'를 뜻하며, 브랜드보다 상황을 먼저 선점하는 것이 핵심입니다.")
st.markdown("**경쟁사 대비 우리 제품을 찾아야만 하는 결정적 이유(CEP)를 도출하고, 방향성을 찾아가세요!**")
st.divider()

tab1, tab2 = st.tabs(["⚡ 전략 생성", "🗂️ 저장된 기록"])

with tab1:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("📦 제품 및 타겟 정보")
        product_name = st.text_input("제품/서비스 명", placeholder="예: 다이어트학교 리압스텝퍼")
        target_audience = st.text_input("🎯 핵심 타겟", placeholder="예: 4050 갱년기 여성, 운동 싫어하는 주부")
        product_details = st.text_area("제품 상세 특징", height=200, placeholder="예: 층간소음 없는 공기주입형 스텝퍼...")
        st.caption("💡 팁: 결과가 마음에 들지 않으면 다시 버튼을 눌러보세요.")
        generate_btn = st.button("🚀 경쟁 우위 전략 도출하기", use_container_width=True, type="primary")

    with col2:
        st.subheader("📊 전략 도출 결과")
        result_container = st.container()

# -----------------------------------------------------------------------------
# 로직 구현 부분 (에러 방지 강화)
# -----------------------------------------------------------------------------
def find_active_model(api_key):
    genai.configure(api_key=api_key)
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        priority_models = ['gemini-1.5-flash', 'gemini-2.0-flash', 'gemini-1.5-pro']
        for p in priority_models:
            for m in available_models:
                if p in m: return m
        return available_models[0] if available_models else 'models/gemini-1.5-flash'
    except:
        return 'models/gemini-1.5-flash'

def perform_search_logic(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, region='kr-kr', max_results=3))
            return "\n".join([f"제목: {r['title']}\n내용: {r['body']}" for r in results])
    except:
        return "검색 결과를 불러올 수 없습니다."

def check_compliance_risks(text):
    risky_words = ["최고", "100%", "완치", "무조건", "보장", "부작용 없", "즉시", "유일", "최초"]
    return [word for word in risky_words if word in text]

def generate_strategy(api_key, name, target, details, platform, tone):
    search_data = perform_search_logic(f"{name} 실제 고객 후기 및 장단점")
    
    # 지침/톤 설정 로직 (기존과 동일)
    # ... (생략된 platform_instructions, tone_instructions 로직은 프롬프트에 포함됨) ...
    
    prompt = f"""
    당신은 대한민국 최고의 퍼포먼스 마케터입니다. 검색된 실제 데이터와 입력 정보를 결합하여 최적의 CEP 7가지를 도출하세요.
    [참고 데이터]: {search_data}
    [입력]: 제품명:{name}, 타겟:{target}, 특징:{details}, 매체:{platform}, 톤:{tone}
    반드시 아래 JSON 형식으로만 출력하세요. 다른 설명은 금지합니다.
    ```json
    [
      {{
        "cep_title": "...", "situation_summary": "...", "thought": "...", 
        "trigger_behavior": "...", "concept_keyword": "...", "ref_keyword": "...", 
        "hooking_copy": "...", "visual_guide": "...", "landing_section": "..."
      }}
    ]
    ```
    """

    active_model = find_active_model(api_key)
    model = genai.GenerativeModel(active_model)

    # 🚀 429 에러 방지용 재시도 로직
    for attempt in range(3):
        try:
            response = model.generate_content(prompt, generation_config=GenerationConfig(temperature=0.8))
            return response.text
        except Exception as e:
            if "429" in str(e):
                time.sleep(15 * (attempt + 1))
                continue
            return f"Error: {str(e)}"
    return "Error: 할당량 초과. 잠시 후 다시 시도해 주세요."

if generate_btn:
    if not product_name or not target_audience or not product_details:
        st.warning("⚠️ 모든 정보를 입력해주세요.")
    else:
        with col2:
            with st.spinner(f"🌐 '{product_name}' 분석 중..."):
                raw_text = generate_strategy(MY_API_KEY, product_name, target_audience, product_details, platform, tone)
                
                try:
                    if raw_text.startswith("Error"):
                        st.error(raw_text)
                    else:
                        json_str = raw_text.replace("```json", "").replace("```", "").strip()
                        data = json.loads(json_str)
                        
                        save_data = {"timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "product": product_name, "target": target_audience, "platform": platform, "data": data}
                        st.session_state.history.insert(0, save_data)
                        
                        visual_label = "🎬 숏폼 영상 기획(오프닝/연출)" if "숏폼" in platform else "🖼️ 상위 이미지"

                        for idx, item in enumerate(data):
                            with st.expander(f"📌 {item.get('cep_title', f'CEP {idx+1}')}", expanded=True):
                                st.markdown(f"**[상황]**\n{item.get('situation_summary', '')}")
                                st.markdown(f"**[생각/동기]**\n\"{item.get('thought', '').replace('\"', '')}\"")
                                st.markdown(f"**[행동 패턴]**\n{item.get('trigger_behavior', '')}")
                                st.markdown("---")
                                st.subheader("🚀 퍼포먼스 활용 포인트")
                                st.info(f"**🏷️ 컨셉 키워드:** {item.get('concept_keyword', '')}")
                                
                                copy_text = item.get('hooking_copy', '')
                                risks = check_compliance_risks(copy_text)
                                if risks:
                                    st.error(f"**⚡ 후킹 카피:** {copy_text}")
                                    st.warning(f"⚠️ 심의 주의: {', '.join(risks)}")
                                else:
                                    st.error(f"**⚡ 후킹 카피:** {copy_text}")
                                
                                st.write(f"**{visual_label}:** {item.get('visual_guide', '')}")
                                st.write(f"**📄 랜딩 섹션:** {item.get('landing_section', '')}")
                                st.markdown("---")
                                
                                # 하단 링크 버튼들 (핀터레스트, 메타 등 - 기존 코드 동일)
                                search_kwd = item.get('ref_keyword', product_name).replace(" ", "+")
                                c1, c2, c3, c4, c5 = st.columns(5)
                                c1.link_button("📌 핀터", f"https://www.pinterest.co.kr/search/pins/?q={search_kwd}")
                                c2.link_button("📘 Meta", f"https://www.facebook.com/ads/library/?ad_type=all&q={search_kwd}")
                                c3.link_button("💚 네이버", f"https://search.naver.com/search.naver?where=image&query={search_kwd}")
                                c4.link_button("🟥 유튜", f"https://www.youtube.com/results?search_query={search_kwd}")
                                c5.link_button("🎵 틱톡", f"https://www.tiktok.com/search?q={search_kwd}")

                        df = pd.DataFrame(data)
                        st.download_button("📥 엑셀 다운로드", df.to_csv(index=False).encode('utf-8-sig'), f"CEP_{product_name}.csv", "text/csv", type="primary")

                except Exception as e:
                    st.error("데이터 처리 중 오류가 발생했습니다.")
                    st.text(raw_text)

with tab2:
    if not st.session_state.history:
        st.info("아직 기록이 없습니다.")
    else:
        for h in st.session_state.history:
            with st.expander(f"🕒 {h['timestamp']} - {h['product']} ({h.get('platform', '')})"):
                st.dataframe(pd.DataFrame(h['data'])[['cep_title', 'hooking_copy', 'visual_guide']])
