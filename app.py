# --- 0. 라이브러리 임포트 ---
import streamlit as st
import random
import pandas as pd # 그래프를 그리기 위해 pandas 라이브러리 추가

# --- CSS 스타일 주입 (버튼 크기 조절) (### <-- 수정됨 (CSS 추가) ###) ---
st.markdown(
    """
    <style>
    /* Streamlit의 모든 버튼을 대상으로 합니다 */
    button {
        font-size: 12px !important; /* 글씨 크기를 12px로 줄임 */
        padding: 4px 8px !important; /* 버튼 내부 여백도 줄임 */
        margin: 0px !important; /* 버튼 간 마진 조절 */
    }
    </style>
    """,
    unsafe_allow_html=True
)
# -------------------------------------


# --- 1. 실제 영상 데이터 (각 12개, 총 36개) ---
image_url_list = {
    "idol": ["images/aespa/1.jpg",
             "images/aespa/2.jpg",
             "images/aespa/3.jpg",
             "images/aespa/4.jpg",
             "images/aespa/5.jpg",
             "images/aespa/6.jpg",
             "images/aespa/7.jpg",
             "images/aespa/8.jpg",
             "images/aespa/9.jpg",
             "images/aespa/10.jpg",
             "images/aespa/11.jpg",
             "images/aespa/12.jpg"
             ],#각각 12개씩 채우기

    "anime":["images/ive/1.jpeg",
             "images/ive/2.jpeg",
             "images/ive/3.jpeg",
             "images/ive/4.jpeg",
             "images/ive/5.jpeg",
             "images/ive/6.jpeg",
             "images/ive/7.jpeg",
             "images/ive/8.jpeg",
             "images/ive/9.jpeg",
             "images/ive/10.jpeg",
             "images/ive/11.jpeg",
             "images/ive/12.jpeg"],

    "news": ["images/lesselafim/1.jpeg",
             "images/lesselafim/2.jpeg",
             "images/lesselafim/3.jpg",
             "images/lesselafim/4.jpeg",
             "images/lesselafim/5.jpeg",
             "images/lesselafim/6.jpeg",
             "images/lesselafim/7.jpeg",
             "images/lesselafim/8.jpeg",
             "images/lesselafim/9.jpeg",
             "images/lesselafim/10.jpeg",
             "images/lesselafim/11.jpeg",
             "images/lesselafim/12.jpeg"],
}

#--------------------------------------

# (교육용 임시 썸네일 이미지를 생성하는 함수)
def get_video_data(category, index):
    """카테고리와 인덱스에 맞는 임시 썸네일 이미지 URL과 정보를 생성합니다."""
    img_url = image_url_list[category][index-1]
    # '뉴스 1번' 영상을 '놓치면 안 되는 중요 뉴스'로 설정
    is_critical = (category == "news" and index == 1)
    title = f"{category.capitalize()} 영상 제목 {index}"
    
    return {"title": title, "img_url": img_url, "is_critical": is_critical}

# VIDEO_DATA 딕셔너리(사전)에 각 카테고리별로 12개의 영상 데이터를 생성
VIDEO_DATA = {
    "idol": [get_video_data("idol", i) for i in range(1, 13)],
    "anime": [get_video_data("anime", i) for i in range(1, 13)],
    "news": [get_video_data("news", i) for i in range(1, 13)],
}

# --- 2. 가중치 정규화 함수 (핵심 로직) ---
def normalize_weights(changed_key=None):
    """
    3개 가중치의 합을 100으로 정규화(Normalize)합니다.
    (반올림 오차는 'idol'이 흡수)
    
    - changed_key (str, optional): 
      'on_change'로 호출될 때, 사용자가 방금 움직인 슬라이더의 key (예: 'idol_weight').
      None이면 '자동 조절'로 간주합니다.
    """
    keys = ['idol_weight', 'anim_weight', 'news_weight']
    
    # --- 2-1. 수동 슬라이더 조작 시 (on_change, changed_key가 있음) ---
    if changed_key:
        # 1. 사용자가 조작한 슬라이더의 현재 값 (예: 아이돌 90)
        changed_value = st.session_state[changed_key]
        # 2. 나머지 두 슬라이더가 나눠 가질 값 (100 - 90 = 10)
        remaining_weight = 100 - changed_value
        
        # 3. 사용자가 조작하지 않은 나머지 두 슬라이더의 key
        other_keys = [k for k in keys if k != changed_key]
        
        # 4. 나머지 두 슬라이더의 '이전' 값과 '이전' 값의 총합
        # (예: 애니 0, 뉴스 20 -> 총합 20)
        old_values = {k: st.session_state[k] for k in other_keys}
        other_total = sum(old_values.values())
        
        new_values = {}
        
        # 5. 다른 슬라이더들의 '이전 비율'에 따라 '남은 가중치(10)'를 분배
        if other_total > 0:
            # (예: 애니 0/20 * 10 = 0, 뉴스 20/20 * 10 = 10)
            for k in other_keys:
                new_values[k] = int((old_values[k] / other_total) * remaining_weight)
        else:
            # (만약 둘 다 0이었다면, 남은 가중치 10을 1/2씩 분배)
            for k in other_keys:
                new_values[k] = remaining_weight // len(other_keys)

        # 6. 계산된 새 값을 세션 상태에 즉시 적용 (슬라이더가 실시간으로 움직임)
        for k, v in new_values.items():
            st.session_state[k] = v
        
        # 7. int() 반올림으로 발생한 오차(100이 아닐 경우) 계산
        current_total = sum(st.session_state[k] for k in keys)
        delta = 100 - current_total
        
        # 8. 오차(delta)를 '아이돌' 또는 '애니'가 흡수하여 100%를 맞춤
        if delta != 0:
            if changed_key != 'idol_weight':
                st.session_state.idol_weight += delta
            else: # 사용자가 '아이돌'을 조작 중이었다면 '애니'가 흡수
                st.session_state.anim_weight += delta

    # --- 2-2. 자동(피드 클릭) 조작 시 (changed_key=None) ---
    else:
        # (예: 아이돌 33+20, 애니 33, 뉴스 34 -> 총합 120)
        total = st.session_state.idol_weight + st.session_state.anim_weight + st.session_state.news_weight
        if total == 0: 
            st.session_state.idol_weight = 33 
            st.session_state.anim_weight = 33 
            st.session_state.news_weight = 34
            return

        # 100% 비율로 다시 계산
        idol_w_new = int((st.session_state.idol_weight / total) * 100)
        anim_w_new = int((st.session_state.anim_weight / total) * 100)
        news_w_new = int((st.session_state.news_weight / total) * 100)
        
        delta = 100 - (idol_w_new + anim_w_new + news_w_new)
        
        # 오차는 '아이돌'이 흡수
        st.session_state.idol_weight = idol_w_new + delta 
        st.session_state.anim_weight = anim_w_new
        st.session_state.news_weight = news_w_new

# --- 3. 가중치 조절 함수 (피드 클릭용) ---

def update_history():
    """가중치 변화 기록을 history 리스트에 추가합니다."""
    st.session_state.step_count += 1
    new_record = {
        "클릭 횟수": st.session_state.step_count,
        "🎵 아이돌": st.session_state.feed_idol_weight,
        "🐰 캐릭터": st.session_state.feed_anim_weight,
        "🕹️ 게임": st.session_state.feed_news_weight
    }


    # 'weight_history' 리스트에 현재 가중치 상태를 딕셔너리로 저장
    st.session_state.weight_history.append(new_record)

def adjust_weights(choice_type):
    """(시청) 가중치에 +20 '부스트'를 주고 정규화합니다."""
    CLICK_BOOST = 20 # 시청 시 20 증가
    
    if choice_type == "idol":
        st.session_state.idol_weight = min(100, st.session_state.idol_weight + CLICK_BOOST)
    elif choice_type == "anime":
        st.session_state.anim_weight = min(100, st.session_state.anim_weight + CLICK_BOOST)
    elif choice_type == "news":
        st.session_state.news_weight = min(100, st.session_state.news_weight + CLICK_BOOST)
    
    normalize_weights() # '자동' 모드로 100% 정규화
    
    # '피드 생성용' 가중치에도 즉시 동기화
    st.session_state.feed_idol_weight = st.session_state.idol_weight
    st.session_state.feed_anim_weight = st.session_state.anim_weight
    st.session_state.feed_news_weight = st.session_state.news_weight
    update_history() # 그래프 기록 추가

def decrease_weights(choice_type):
    """(관심 없음) 가중치에 -10 '패널티'를 주고 정규화합니다."""
    CLICK_PENALTY = 10 # 관심 없음 시 10 감소
    
    if choice_type == "idol":
        st.session_state.idol_weight = max(0, st.session_state.idol_weight - CLICK_PENALTY)
    elif choice_type == "anime":
        st.session_state.anim_weight = max(0, st.session_state.anim_weight - CLICK_PENALTY)
    elif choice_type == "news":
        st.session_state.news_weight = max(0, st.session_state.news_weight - CLICK_PENALTY)
    
    normalize_weights() 
    
    st.session_state.feed_idol_weight = st.session_state.idol_weight
    st.session_state.feed_anim_weight = st.session_state.anim_weight
    st.session_state.feed_news_weight = st.session_state.news_weight
    update_history() # 그래프 기록 추가

# --- 4. 피드 생성 함수 ---
def generate_feed(idol_w, anim_w, news_w): 
    """
    현재 가중치에 따라 12개의 피드 리스트를 생성합니다.
    """
    feed_slots = 12 
    feed_list = []
    
    # 가중치(%)에 따라 12개 중 몇 개를 할당할지 계산
    idol_count = round(feed_slots * (idol_w / 100))
    anim_count = round(feed_slots * (anim_w / 100))
    news_count = feed_slots - idol_count - anim_count # 총합 12개

    # 중요 뉴스(스쿨존) 데이터 가져오기
    critical_news_data = VIDEO_DATA["news"][0] 
    has_critical_news = False

    # 뉴스 가중치가 있고, 뉴스 슬롯이 1개 이상이면 중요 뉴스를 1개 '무조건' 포함
    if news_w > 0 and news_count > 0:
        feed_list.append(critical_news_data)
        news_count -= 1 # (슬롯 1개 사용)
        has_critical_news = True

    # random.sample: VIDEO_DATA에서 중복 없이 랜덤으로 영상을 뽑음
    feed_list += random.sample(VIDEO_DATA["idol"], min(idol_count, len(VIDEO_DATA["idol"])))
    feed_list += random.sample(VIDEO_DATA["anime"], min(anim_count, len(VIDEO_DATA["anime"])))
    
    # 중요 뉴스를 제외한 '일반 뉴스' 목록
    other_news_data = [item for item in VIDEO_DATA["news"] if not item.get("is_critical")]
    if other_news_data:
        feed_list += random.sample(other_news_data, min(news_count, len(other_news_data)))
    elif news_count > 0: # (일반 뉴스가 없으면 스쿨존 뉴스로 마저 채움)
        feed_list.append(critical_news_data) 
    
    # 만약 12개가 안 채워졌으면(반올림 오차 등), 아이돌 영상으로 마저 채움
    while len(feed_list) < feed_slots:
        feed_list.append(random.choice(VIDEO_DATA["idol"])) 
    
    feed_list = feed_list[:feed_slots] # 12개로 자르기
    random.shuffle(feed_list) # 피드 순서 섞기
    
    # 최종 피드에 '중요 뉴스'가 포함되었는지 여부 반환
    final_has_critical_news = any(item.get("is_critical") for item in feed_list)
    
    return feed_list, final_has_critical_news

# --- 5. Streamlit 앱 메인 ---
st.set_page_config(layout="wide") # 넓은 화면 사용
st.markdown(
    """
    <div style='
        text-align: center; 
        background-color: #fff0f0;  /* 연한 분홍*/
        padding: 10px;
        border-radius: 0px;
    '>
    <h1 style='color: #333333;           
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);  
        border:5px solid  #ffc1b6;
        border-radius: 10px;
    '>🎬 추천 알고리즘 시뮬레이터</h1>
    </div>
    """,
    unsafe_allow_html=True
)


# 페이지 전체를 90% 너비로 제한하고 중앙 정렬
st.markdown(
    """
    <style>
    .appview-container .main {
        max-width: 90%;
        margin: 0 auto;
        background-color: #ffe4e1;
    }
    </style>
    """,
    unsafe_allow_html=True
)





# --- 세션 상태 초기화 ---
# (st.session_state: Streamlit이 새로고침 되어도 값을 기억하는 저장소)
if 'idol_weight' not in st.session_state:
    # 'idol_weight' 등: 슬라이더가 보여주는 값 (실시간 연동)
    st.session_state.idol_weight = 33 
    st.session_state.anim_weight = 33 
    st.session_state.news_weight = 34
    # 'feed_idol_weight' 등: 피드 생성에 실제 사용되는 값 (적용 버튼 눌러야 동기화)
    st.session_state.feed_idol_weight = 33
    st.session_state.feed_anim_weight = 33
    st.session_state.feed_news_weight = 34
    st.session_state.reset_flag = False # 초기화 버튼 플래그
    st.session_state.weight_history = [] # 그래프 기록용 리스트
    st.session_state.step_count = 0 # 그래프 x축 (클릭 횟수)
    # 그래프의 시작점 (0번 클릭) 기록
    st.session_state.weight_history.append({
        "클릭 횟수": 0,
        "🎵 아이돌": 33,
        "🐰 캐릭터": 33,
        "🕹️ 게임": 34
    })
if 'alert_shown' not in st.session_state:
    st.session_state.alert_shown = None # 팝업 중복 방지

# '초기화' 버튼 클릭 시, 'reset_flag'가 True가 됨
if st.session_state.get('reset_flag', False):
    st.session_state.idol_weight = 33
    st.session_state.anim_weight = 33
    st.session_state.news_weight = 34
    st.session_state.feed_idol_weight = 33 
    st.session_state.feed_anim_weight = 33
    st.session_state.feed_news_weight = 34
    st.session_state.alert_shown = None
    st.session_state.weight_history = [] # 기록 초기화
    st.session_state.step_count = 0
    st.session_state.weight_history.append({
        "클릭 횟수": 0,
        "🎵 아이돌": 33,
        "🐰 캐릭터": 33,
        "🕹️ 게임": 34
    })
    st.session_state.reset_flag = False # 플래그 다시 내리기


#st.markdown("---") # 구분선

# --- 6. 화면 분할 레이아웃 ---
# 화면을 2:1 비율로 분할 (왼쪽: 피드, 오른쪽: 제어판)
left_col, right_col = st.columns([2, 1]) 


# --- 7. 왼쪽 컬럼 (피드) ---
with left_col:

    #제목이랑 피드 사이의 간격 생성 
    st.markdown(
        """
        <h3>    </h2>
        """,
        unsafe_allow_html=True
    )

    
# ---7-1. 피드 생성란 ---
    # '피드 생성용' 가중치 (feed_idol_weight)를 기준으로 피드 생성
    feed_list, has_critical_news = generate_feed(
        st.session_state.feed_idol_weight,
        st.session_state.feed_anim_weight,
        st.session_state.feed_news_weight
    ) 

    cols = st.columns(4) # 4열 (4x3 그리드)
    

    for i, video in enumerate(feed_list):

        # 영상 데이터(딕셔너리)를 기반으로 content_type 식별
        content_type = "unknown" 
        if any(v["title"] == video["title"] for v in VIDEO_DATA["idol"]):
            content_type = "idol"
        elif any(v["title"] == video["title"] for v in VIDEO_DATA["anime"]):
            content_type = "anime"
        elif any(v["title"] == video["title"] for v in VIDEO_DATA["news"]):
            content_type = "news"

        with cols[i % 4]: # 0,1,2,3 / 0,1,2,3 ... 순으로 열에 배치
            st.image(video["img_url"], width=150, use_container_width=True) 
            
            # '시청' / '관심 없음' 버튼을 2열로 분리
            btn_cols = st.columns(2)
            with btn_cols[0]:
                button_label = f"💖좋아요" if content_type == "idol" else \
                               f"💖좋아요" if content_type == "anime" else \
                               f"💖좋아요"
                # '시청' 버튼: 클릭 시(on_click) adjust_weights 함수 호출
                if st.button(button_label, key=f"btn_{i}", 
                             on_click=adjust_weights, args=(content_type,)):
                    st.session_state.alert_shown = None # 팝업 초기화
                    st.rerun() # 앱 새로고침
            
            with btn_cols[1]:
                # '관심 없음' 버튼: 클릭 시(on_click) decrease_weights 함수 호출
                if st.button("관심❌", key=f"dismiss_{i}", 
                             on_click=decrease_weights, args=(content_type,)):
                    st.session_state.alert_shown = None
                    st.rerun()
            
            # (피드 카드 사이의 간격이 너무 벌어져서 제거)
            # st.markdown("---") 



# ---7-2. 현재 상태 경고란 ---
    WARNING_THRESHOLD = 15 # 경고 기준선
    alerts_to_show = [] # 팝업에 띄울 경고 목록
    is_balanced = True # '균형 잡힘' 상태인지 확인

    # '피드 생성용' 가중치(feed_idol_weight 등)를 기준으로 검사
    if st.session_state.feed_news_weight < WARNING_THRESHOLD:
        is_balanced = False 
        alerts_to_show.append("news") 
    
        if not has_critical_news: # '게임'를 놓쳤을 때
            st.error(f"🚨 필터버블 발생!!! 배제된 피드: 게임피드({st.session_state.feed_news_weight}%)")
        else: # 가중치는 낮지만 '중요 뉴스'가 운 좋게 포함됐을 때
            st.error(f"🚨 필터버블 발생!!! 배제된 피드: 게임피드({WARNING_THRESHOLD}% 미만)")

    if st.session_state.feed_idol_weight < WARNING_THRESHOLD:
        is_balanced = False 
        st.error(f"🚨 필터버블 발생!!! 배제된 피드: 아이돌 피드({WARNING_THRESHOLD}% 미만)")
        alerts_to_show.append("idol") 

    if st.session_state.feed_anim_weight < WARNING_THRESHOLD:
        is_balanced = False 
        st.error(f"🚨 필터버블 발생!!! 배제된 피드: 캐릭터 피드({WARNING_THRESHOLD}% 미만)")
        alerts_to_show.append("anime") 

    # 위 3개 검사에서 모두 통과(is_balanced = True)했을 때만 성공 메시지
    if is_balanced:
        st.success("🎉 잘하고있어요! 정보를 골고루 탐색하고있어요!!.")
        st.session_state.alert_shown = "success" 


# --- 8. 오른쪽 컬럼 (제어판) ---
with right_col:

# --- 8-1. 가중치 조정 슬라이드 ---
    st.markdown(
    """
    <div style='
        background-color:  #fff0f0;  /* 살짝 진한 회색 */
        padding: 8px;
        border-radius: 5px;
        margin-bottom: 10px;
    '>
        <h3 style='text-align: center;'>🖱️ 가중치 조정 슬라이드</h3>
    </div>
    """, 
    unsafe_allow_html=True
)

    # 슬라이더는 'idol_weight'에 연결
    # 값이 변경될 때마다(on_change) normalize_weights 함수를 '수동' 모드로 호출
    st.slider(
        "🎵 아이돌", 0, 100,
        key="idol_weight",
        on_change=normalize_weights, args=('idol_weight',)
    )
    st.slider(
        "🐰 캐릭터", 0, 100,
        key="anim_weight",
        on_change=normalize_weights, args=('anim_weight',)
    )
    st.slider(
        "🕹️ 게임", 0, 100,
        key="news_weight",
        on_change=normalize_weights, args=('news_weight',)
    )
    
    
    col1, col2,col3,col4 = st.columns(4)  # 4개의 열 생성, 버튼의 간격 조정용
    with col2:
        # (### <-- 수정됨 ###) width 파라미터 제거 (CSS가 처리)
        if st.button("적용하기"):
            st.session_state.feed_idol_weight = st.session_state.idol_weight
            st.session_state.feed_anim_weight = st.session_state.anim_weight
            st.session_state.feed_news_weight = st.session_state.news_weight
            st.session_state.alert_shown = None
            update_history()  # 수동 적용도 그래프에 기록
            st.rerun()  # 피드를 업데이트하기 위해 rerun

    with col3:
        # (### <-- 수정됨 ###) width 파라미터 제거 (CSS가 처리)
        if st.button("🔄 초기화"):
            st.session_state.reset_flag = True  # 리셋 플래그 켜기
            st.rerun()


# --- 8-2. 가중치 변화 그래프 ---

    st.markdown(
        """
        <div style='
            background-color:  #fff0f0;  /* 살짝 진한 회색 */
            padding: 8px;
            border-radius: 5px;
            margin-top: 50px;'>
            <h3 style='text-align: center;'>📊 가중치 변화 그래프</h3>
        </div>
        """, 
        unsafe_allow_html=True
        )
    
    if len(st.session_state.weight_history) > 1: # 기록이 2개 이상일 때만 그림
        # history 리스트를 pandas DataFrame으로 변환
        chart_data = pd.DataFrame(st.session_state.weight_history).set_index("클릭 횟수")
        # 라인 차트 생성 (색상 지정)
        st.line_chart(chart_data, color=["#FF69B4", "#87CEEB", "#FF4500"]) 
    else:
        st.info("피드를 클릭하거나 가중치를 적용하면 그래프가 표시됩니다.")

    st.markdown("---")


# 9. 'st.dialog' 중앙 팝업 알림 (한 번만 띄우기)
# (경고 목록을 문자열로 변환하여, 이전에 띄운 팝업과 동일한지 비교)
alert_signature = ",".join(sorted(alerts_to_show))

if alerts_to_show and st.session_state.alert_shown != alert_signature:
    
    @st.dialog("🚨 경고: 필터버블 감지! 정보를 편식하고있어요!!")
    def show_alert():
        # alerts_to_show 리스트에 있는 모든 경고를 팝업에 표시
        if "news" in alerts_to_show:
            st.image(get_video_data("news", 1)["img_url"], width=100)
            st.error(f"**배제된 피드 발생!! : 게임 피드({st.session_state.feed_news_weight}%)**")
            st.write("---")
        
        if "idol" in alerts_to_show:
            st.image(get_video_data("idol", 1)["img_url"], width=100)
            st.error(f"**배제된 피드 발생!! : 아이돌 피드({st.session_state.feed_idol_weight}%)**")
            st.write("---")

        if "anime" in alerts_to_show:
            st.image(get_video_data("anime", 1)["img_url"], width=100)
            st.error(f"**배제된 피드 발생!! : 캐릭터 피드({st.session_state.feed_anim_weight}%)**")
            st.write("---")
        
        if st.button("확인했어요, 다른 정보도 골고루 보러 가기"):
            st.session_state.alert_shown = alert_signature # '확인' 누름을 기록
            st.rerun()

    show_alert()