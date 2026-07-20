import pandas as pd 
import streamlit as st
import plotly.express as px

# 1. 페이지 설정 (넓은 레이아웃)
st.set_page_config(page_title="지역별 월세 임대료 분석 대시보드", layout="wide")

st.title("🏢 서울시 자치구/법정동별 월세 및 건물 현황 대시보드")
st.caption("선택한 지역의 월세 기준 평당 가격 중앙값, 보증금, 건물 나이, 지하 여부 및 가격 범위를 분석합니다.")

# 2. 데이터 불러오기 함수
@st.cache_data
def load_data():
    url = f"https://drive.google.com/file/d/1MdrrlHFduPXyV2oazxCFV0nmeYagtnVx/view?usp=drive_link"
    df = pd.read_csv(url)
    
    # '월세' 데이터만 필터링 (전월세구분 컬럼이 있는 경우)
    if '전월세구분' in df.columns:
        df = df[df['전월세구분'] == '월세']
    
    # 지하여부 컬럼 문자열 보정
    if '지하여부' in df.columns:
        df['지하여부_표시'] = df['지하여부'].apply(lambda x: '지하/반지하' if x in [1, True, '지하', '반지하', '지하/반지하'] else '지상')
    
    return df

# 데이터 로딩
try:
    df = load_data()
except Exception as e:
    st.error(f"CSV 파일을 불러오는 중 오류가 발생했습니다. 파일명을 확인해 주세요. 오류: {e}")
    st.stop()

# 3. 사이드바 - 자치구 및 법정동 필터링 ('전체' 옵션 포함)
st.sidebar.header("📍 지역 선택")

# 자치구 선택 ('전체' 옵션 추가)
gu_list = ["전체"] + sorted(df['자치구명'].dropna().unique().tolist())
selected_gu = st.sidebar.selectbox("자치구 선택", gu_list)

# 선택된 자치구에 맞춰 법정동 목록 생성 ('전체' 옵션 추가)
if selected_gu == "전체":
    dong_list = ["전체"] + sorted(df['법정동명'].dropna().unique().tolist())
else:
    dong_list = ["전체"] + sorted(df[df['자치구명'] == selected_gu]['법정동명'].dropna().unique().tolist())

selected_dong = st.sidebar.selectbox("법정동 선택", dong_list)

# 4. 선택 조건에 따른 데이터 필터링
sub_df = df.copy()

if selected_gu != "전체":
    sub_df = sub_df[sub_df['자치구명'] == selected_gu]

if selected_dong != "전체":
    sub_df = sub_df[sub_df['법정동명'] == selected_dong]

# 제목 타이틀 동적 변경
region_title = f"{selected_gu if selected_gu != '전체' else '서울시 전체'} {selected_dong if selected_dong != '전체' else ''}".strip()
st.subheader(f"📌 {region_title} 월세 분석 결과 ({len(sub_df):,} 건)")

if sub_df.empty:
    st.warning("선택하신 지역에 해당하는 월세 데이터가 존재하지 않습니다.")
else:
    # 5. 주요 지표 (Metrics) - 4개 카드로 배치
    col1, col2, col3, col4 = st.columns(4)
    
    # 평당 가격 중앙값
    median_py_price = sub_df['평당가격'].median() if '평당가격' in sub_df.columns else 0
    
    # 보증금 중앙값
    median_deposit = sub_df['보증금(만원)'].median() if '보증금(만원)' in sub_df.columns else 0
    
    # 건물 나이 평균
    avg_building_age = sub_df['건물나이'].mean() if '건물나이' in sub_df.columns else 0
    
    # 지하/반지하 가구 수 및 비율
    basement_cnt = (sub_df['지하여부_표시'] == '지하/반지하').sum() if '지하여부_표시' in sub_df.columns else 0
    basement_ratio = (basement_cnt / len(sub_df)) * 100 if len(sub_df) > 0 else 0

    with col1:
        st.metric(label="💵 평당 가격 (중앙값)", value=f"{median_py_price:,.1f} 만원")
    with col2:
        st.metric(label="🏦 보증금 (중앙값)", value=f"{median_deposit:,.0f} 만원")
    with col3:
        st.metric(label="🏗️ 평균 건물 나이", value=f"{avg_building_age:.1f} 년")
    with col4:
        st.metric(label="🏚️ 지하/반지하 비중", value=f"{basement_ratio:.1f}%", delta=f"총 {basement_cnt} 건")

    st.divider()

    # 6. 최저 / 최대 가격 범위
    st.markdown("### 🏷️ 가격 범위 (최저 ~ 최대)")
    p_col1, p_col2, p_col3 = st.columns(3)
    
    with p_col1:
        min_dep = sub_df['보증금(만원)'].min()
        max_dep = sub_df['보증금(만원)'].max()
        st.info(f"**보증금 범위**\n\n최저 **{min_dep:,.0f}** 만원 ~ 최고 **{max_dep:,.0f}** 만원")
        
    with p_col2:
        min_rent = sub_df['임대료(만원)'].min()
        max_rent = sub_df['임대료(만원)'].max()
        st.success(f"**월세(임대료) 범위**\n\n최저 **{min_rent:,.0f}** 만원 ~ 최고 **{max_rent:,.0f}** 만원")
        
    with p_col3:
        min_py = sub_df['평당가격'].min()
        max_py = sub_df['평당가격'].max()
        st.warning(f"**평당가격 범위**\n\n최저 **{min_py:,.1f}** 만원 ~ 최고 **{max_py:,.1f}** 만원")

    st.divider()

    # 7. 인터랙티브 차트 시각화
    c_col1, c_col2 = st.columns(2)
    
    with c_col1:
        st.markdown("#### 📊 보증금 vs 월세 분포 (점 크기: 평수)")
        fig_scatter = px.scatter(
            sub_df, 
            x="보증금(만원)", 
            y="임대료(만원)", 
            size="평수" if "평수" in sub_df.columns else None,
            color="지하여부_표시" if "지하여부_표시" in sub_df.columns else None,
            hover_data=["건물용도", "건물나이", "층"],
            title="보증금 대비 월세 분포"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    with c_col2:
        st.markdown("#### 🏢 건물 용도별 분포")
        fig_pie = px.pie(
            sub_df, 
            names="건물용도", 
            title="선택 지역 건물 용도 비율",
            hole=0.4
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # 8. 선택 지역 상세 데이터 보기
    with st.expander("📄 선택 지역 원본 상세 데이터 보기"):
        st.dataframe(sub_df)