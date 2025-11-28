import streamlit as st
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
import pandas as pd
import json
import datetime
from duckduckgo_search import DDGS 

# -----------------------------------------------------------------------------
# [진단 모드] 라이브러리 버전 확인 (화면 상단 출력)
# -----------------------------------------------------------------------------
# 이 코드는 현재 서버에 설치된 버전을 눈으로 확인시켜줍니다.
st.set_page_config(page_title="CEP 퍼포먼스 마케팅 솔루션 Master", page_icon="🌐", layout="wide")

try:
    version = genai.__version__
    # 버전이 낮으면 경고, 높으면 통과
    if version < "0.7.0":
        st.error(f"🚨 현재 설치된 구글 AI 버전: {version} (구버전입니다. 앱을 삭제 후 재배포하세요!)")
    else:
        # 정상일 경우 이 부분은 사용자에게 안 보이게 처리하거나 작게 표시
        pass 
except:
    st.error("🚨 구글 AI 라이브러리가 설치되지 않았습니다.")

# -----------------------------------------------------------------------------
# [보안] 비밀번호 & API 키 설정
# -----------------------------------------------------------------------------
try:
    MY_API_KEY = st.secrets["GOOGLE_API_KEY"]
    TEAM_PASSWORD = st.secrets["TEAM_PASSWORD"]
except FileNotFoundError:
    st.error("🚨 서버 설정 오류: Secrets에 API 키와 비밀번호가 설정되지 않았습니다.")
    st.stop()

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
                st.caption("CCFM 전용 접속 코드를 입력하세요.")
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
# 메인 앱 코드
# =============================================================================

@st.dialog("💡 이 프로그램의 핵심")
def show_cep_guide():
    st.markdown(
        """
        ### 1️⃣ 직접 검색 기반 분석 (Search Agent)
        이 프로그램은 AI가 상상하는 것이 아니라, 실제 웹 검색(리뷰, 기사, 경쟁사)을 수행하여 데이터를 수집한 뒤 분석합니다.
        
        ### 2️⃣ 무엇을 얻을 수 있나요?
        **'뇌피셜'이 아닌 '팩트(Fact)'에 기반한** 날카로운 경쟁 우위 전략과 CEP를 도출합니다.
        
        ### 3️⃣ 활용 가이드
        검색 시간이 30초 정도 더 소요될 수 있으나, 결과의 퀄리티는 훨씬 높습니다.
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
    st.success("✅ Real-time Search 활성화")
    
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
    
    with st.expander("💡 업데이트 노트 (Real Search)"):
        st.info(
            """
            **[직접 검색 엔진 탑재]**
            이제 프로그램이 직접 인터넷을 검색하여 최신 리뷰와 경쟁사 동향을 긁어옵니다.
            Gemini는 이 '실제 데이터'를 읽고 분석하므로 훨씬 정확합니다.
            """
        )
    
    st.caption("Developed for **Performance Marketers & Designers**")

st.title("🌐 CEP 퍼포먼스 마케팅 솔루션")

st.info("💡 **CEP(Category Entry Point)란?** 소비자가 구매를 결심하는 '결정적 계기(상황)'를 뜻하며, 브랜드보다 상황을 먼저 선점하는 것이 핵심입니다.")

st.markdown(
    """
    **AI를 100% 신뢰하지 마세요! 새로운 아이디어로만 참고하고 더 디벨롭 해주세요.**
    """
)

st.divider()

tab1, tab2 = st.tabs(["⚡ 전략 생성", "🗂️ 저장된 기록"])

with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📦 제품 및 타겟 정보")
        
        product_name = st.text_input("제품/서비스 명 (정확히 입력)", placeholder="예: 다이어트학교 리압스텝퍼")
        target_audience = st.text_input("🎯 핵심 타겟", placeholder="예: 4050 갱년기 여성, 운동 싫어하는 주부")
        product_details = st.text_area(
            "제품 상세 특징 (추가 정보)", 
            placeholder="제품의 고유한 강점이나 이벤트 정보를 적어주시면 검색 결과와 결합하여 분석합니다.",
            height=200
        )
        
        st.caption("💡 팁1: 제품명을 정확히 적어야 AI가 웹사이트와 후기를 제대로 찾아냅니다.")
        st.caption("💡 팁2: 원하는 전략이 안보이시나요? 다시 버튼을 눌러 새로운 전략을 확인하세요.")
        
        generate_btn = st.button("🚀 웹 분석 및 전략 도출하기", use_container_width=True, type="primary")

    with col2:
        st.subheader("📊 전략 도출 결과")
        result_container = st.container()

# -----------------------------------------------------------------------------
# Backend Logic
# -----------------------------------------------------------------------------
def perform_web_search(query, max_results=3):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, region='kr-kr', safesearch='off', max_results=max_results))
            search_summary = ""
            for idx, res in enumerate(results):
                search_summary += f"[{idx+1}] 제목: {res['title']}\n내용: {res['body']}\n링크: {res['href']}\n\n"
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
            json_str = text[start_idx : end_idx + 1]
            return json.loads(json_str)
        else:
            clean_text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
    except Exception as e:
        raise Exception(f"JSON 파싱 실패: {str(e)}")

def generate_strategy(api_key, name, target, details, platform, tone):
    
    # 1. [검색 단계]
    search_query_1 = f"{name} 후기 장단점"
    search_query_2 = f"{name} 상세페이지 특징"
    
    search_result_1 = perform_web_search(search_query_1)
    search_result_2 = perform_web_search(search_query_2)
    
    collected_data = f"""
    **[웹 검색 결과 1: 실제 고객 후기]**
    {search_result_1}
    
    **[웹 검색 결과 2: 제품 특징]**
    {search_result_2}
    """

    # 2. [프롬프트 작성]
    platform_instructions = ""
    if "GFA/배너" in platform:
        platform_instructions = """
        **[🚨 중요: GFA/카카오 배너 매체 규격 준수]**
        1. **글자 수 제한**: 메인 카피는 띄어쓰기 포함 **25자 이내**로 작성하세요. 길어지면 잘립니다.
        2. **금지어**: '좋아요', '댓글', '공유' 언급 절대 금지.
        3. **스타일**: '뉴스 기사 헤드라인' 또는 '커뮤니티 썰' 느낌의 텍스트형 배너 카피.
        """
    elif "숏폼" in platform:
        platform_instructions = """
        **[🚨 중요: 숏폼(릴스/틱톡) 매체 규격 준수]**
        1. **형식**: 글자가 아닌 '영상 연출(Action)' 위주.
        2. **Visual Guide**: 정지 이미지가 아니라, 초반 3초에 시선을 뺏는 구체적인 행동 지시문 작성.
        3. **카피**: 자막으로 들어갈 짧은 구어체.
        """
    elif "피드" in platform:
        platform_instructions = """
        **[🚨 중요: 인스타/페북 피드 매체 규격 준수]**
        1. **형식**: 카드뉴스 표지(썸네일).
        2. **글자 수 제한**: 가독성을 위해 2줄 이내로 끊어지는 짧고 굵은 헤드라인.
        """
    else:
        platform_instructions = """
        **[🚨 중요: 검색광고(TDA) 매체 규격 준수]**
        1. **글자 수 제한**: 제목 15자 이내.
        2. **스타일**: 검색 키워드를 반드시 포함한 신뢰도 높은 문구.
        """

    compliance_instructions = """
    **[⚠️ 심의/반려 주의 (Compliance Check)]**
    - 표시광고법 및 의료법 위반 소지가 있는 단어('최고', '100%', '완치', '무조건', '보장', '부작용 없음')는 절대 사용하지 마세요.
    """

    tone_instructions = ""
    if "매운맛" in tone:
        tone_instructions = "**[🔥 톤앤매너: 극도로 매운맛]** 점잖은 경고 금지. '당신 지금 돈 버리고 있다', '망가지는 중이다' 처럼 손실 회피를 강하게 자극하세요."
    elif "순한맛" in tone:
        tone_instructions = "**[💧 톤앤매너: 순한맛]** 고객의 아픔에 공감하고 따뜻한 해결책을 제시하세요."
    else:
        tone_instructions = "**[💡 톤앤매너: 논리적]** 객관적 사실과 기능적 우위를 강조하세요."

    prompt = f"""
    당신은 대한민국 최고의 퍼포먼스 마케터이자 카피라이터입니다.
    
    **[참고 자료: 실시간 웹 검색 데이터]**
    {collected_data}
    
    ---

    **[미션]**
    위 검색 데이터와 아래 입력 정보를 결합하여 **최적의 CEP(Category Entry Point) 7가지**를 도출하세요.

    [입력 정보]
    - 제품명: {name}
    - 타겟: {target}
    - 상세 특징(참고): {details}
    - **선택된 매체**: {platform}
    - **선택된 톤**: {tone}

    {platform_instructions}
    {compliance_instructions}
    {tone_instructions}

    [최종 출력 포맷 (JSON)]
    위 사고 과정을 통해 도출된 내용을 **오직 JSON 형식으로만** 출력하세요. 서론이나 부연 설명은 금지합니다.
    
    **[중요: 검색 키워드 추출]**
    `ref_keyword` 필드에는 제품명(예: 리압스텝퍼)이 아닌, **광고 라이브러리에서 검색했을 때 레퍼런스가 많이 나올 법한 '대표 카테고리 키워드'(예: 다이어트, 붓기, 홈트레이닝)** 를 1개만 단답형으로 적으세요.

    ```json
    [
      {{
        "cep_title": "CEP N. [상황]과 [동기]를 결합한 직관적인 타이틀",
        "situation_summary": "웹 검색 데이터와 7W 분석을 토대로 작성된 구체적인 상황 묘사 (1~2문장)",
        "thought": "고객의 속마음/동기 (따옴표 포함한 독백)",
        "trigger_behavior": "검색 키워드 및 행동 패턴 (화살표 활용)",
        "concept_keyword": "컨셉 키워드 (해시태그)",
        "ref_keyword": "레퍼런스 검색용 대표 키워드 (예: 다이어트)",
        "hooking_copy": "타겟 저격 후킹 카피 (매체 규격 준수)",
        "visual_guide": "매체 맞춤형 시각적 가이드",
        "landing_section": "랜딩 페이지 구성 아이디어"
      }},
      ...
    ]
    ```
    """
    
    genai.configure(api_key=api_key)
    
    # [🔥 핵심 수정] 모델 자동 전환 로직 강화
    # 1.5-flash -> 1.5-pro -> 1.0-pro 순으로 시도
    # 각 모델별로 지원하는 기능을 자동으로 감지하여 에러 회피
    
    try:
        # 1차 시도: 1.5-flash
        model = genai.GenerativeModel('gemini-1.5-flash')
        config = GenerationConfig(temperature=1.0) 
        response = model.generate_content(prompt, generation_config=config)
        return response.text
    except:
        try:
            # 2차 시도: 1.5-pro
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(prompt)
            return response.text
        except:
            try:
                # 3차 시도: 1.0-pro (가장 안정적)
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                return f"Error: 모든 모델 연결 실패. ({str(e)})"

if generate_btn:
    if not product_name or not target_audience or not product_details:
        st.warning("⚠️ 모든 정보를 입력해주세요.")
    else:
        with col2:
            with st.spinner(f"🌐 '{product_name}' 웹 검색 및 경쟁사 분석 중..."):
                raw_text = generate_strategy(MY_API_KEY, product_name, target_audience, product_details, platform, tone)
                
                try:
                    if raw_text.startswith("Error"):
                        st.error("🚨 AI 처리 중 오류가 발생했습니다.")
                        st.error(raw_text)
                    else:
                        data = extract_json_from_text(raw_text)
                        
                        save_data = {
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "product": product_name,
                            "target": target_audience,
                            "platform": platform,
                            "data": data
                        }
                        st.session_state.history.insert(0, save_data)
                        
                        visual_label = "🖼️ 상위 이미지"
                        if "숏폼" in platform:
                            visual_label = "🎬 숏폼 영상 기획(오프닝/연출)"

                        for idx, item in enumerate(data):
                            cep_title_text = f"📌 {item.get('cep_title', f'CEP {idx+1}')}"
                            with st.expander(cep_title_text, expanded=True):
                                
                                st.markdown(f"### {item.get('cep_title', '')}")
                                
                                st.markdown(f"**[상황]**")
                                st.write(item.get('situation_summary', '내용 없음'))
                                
                                st.markdown(f"**[생각/동기]**")
                                thought_content = item.get('thought', '').replace('"', '')
                                st.write(f'"{thought_content}"')
                                
                                st.markdown(f"**[카테고리 진입 계기(행동)]**")
                                st.write(item.get('trigger_behavior', '내용 없음'))
                                
                                st.markdown("---")
                                
                                st.markdown("##### 🚀 퍼포먼스 활용 포인트")
                                st.info(f"**🏷️ 컨셉 키워드:** {item.get('concept_keyword', '키워드 없음')}")
                                
                                copy_text = item.get('hooking_copy', '')
                                risks = check_compliance_risks(copy_text)
                                
                                if risks:
                                    st.error(f"**⚡ 후킹 카피:** {copy_text}")
                                    st.warning(f"⚠️ **[주의]** 심의 반려 위험 단어 감지: {', '.join(risks)}")
                                else:
                                    st.error(f"**⚡ 후킹 카피:** {copy_text}")
                                
                                st.write(f"**{visual_label}:** {item.get('visual_guide', '')}")
                                st.write(f"**📄 랜딩 섹션:** {item.get('landing_section', '')}")
                                
                                st.markdown("---")
                                
                                st.markdown("**📚 디자인 레퍼런스 검색**")
                                search_kwd = item.get('ref_keyword', item.get('concept_keyword', product_name))
                                search_kwd_encoded = search_kwd.replace(" ", "+")
                                
                                col_ref1, col_ref2, col_ref3, col_ref4, col_ref5 = st.columns(5)
                                with col_ref1:
                                    st.link_button("📌 핀터레스트", f"https://www.pinterest.co.kr/search/pins/?q={search_kwd_encoded}")
                                with col_ref2:
                                    st.link_button("📘 Meta 광고", f"https://www.facebook.com/ads/library/?ad_type=all&q={search_kwd_encoded}")
                                with col_ref3:
                                    st.link_button("💚 네이버(Ref)", f"https://search.naver.com/search.naver?where=image&query={search_kwd_encoded}")
                                with col_ref4:
                                    st.link_button("🟥 유튜브", f"https://www.youtube.com/results?search_query={search_kwd_encoded}")
                                with col_ref5:
                                    st.link_button("🎵 틱톡", f"https://www.tiktok.com/search?q={search_kwd_encoded}")
                                
                                st.markdown("**🗣️ 실제 고객 반응(VOC) & 기사 확인**")
                                kwd_for_voc = item.get('concept_keyword', '')
                                voc_query = f"{product_name} {kwd_for_voc}"
                                voc_encoded = voc_query.replace(" ", "+")
                                
                                c1, c2, c3 = st.columns(3)
                                with c1:
                                    st.link_button("🟢 네이버 블로그 후기", f"https://search.naver.com/search.naver?where=blog&query={voc_encoded}")
                                with c2:
                                    st.link_button("☕ 네이버 카페 반응", f"https://search.naver.com/search.naver?where=article&query={voc_encoded}")
                                with c3:
                                    st.link_button("📰 관련 뉴스/기사", f"https://www.google.com/search?q={voc_encoded}&tbm=nws")

                        df = pd.DataFrame(data)
                        csv = df.to_csv(index=False).encode('utf-8-sig')
                        st.download_button("📥 전략 리포트 엑셀 다운로드", csv, f"CEP_Logic_Strategy_{product_name}.csv", "text/csv", type="primary")

                except Exception as e:
                    st.error(f"데이터 처리 중 오류가 발생했습니다. ({str(e)})")
                    st.text("▼ AI가 반환한 원본 데이터 (디버깅용) ▼")
                    st.text(raw_text)

with tab2:
    if not st.session_state.history:
        st.info("아직 기록이 없습니다.")
    else:
        for h in st.session_state.history:
            h_platform = h.get('platform', '일반')
            with st.expander(f"🕒 {h['timestamp']} - {h['product']} ({h_platform})"):
                h_df = pd.DataFrame(h['data'])
                st.download_button("📥 엑셀 다운로드", h_df.to_csv(index=False).encode('utf-8-sig'), f"History_{h['timestamp']}.csv")
                st.dataframe(h_df[['cep_title', 'hooking_copy', 'visual_guide']])
