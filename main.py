import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ── 기본 설정 ──────────────────────────────────────────────
st.set_page_config(page_title="서울 100년 기온 변화", page_icon="🌡️", layout="wide")

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")
    df["날짜"] = pd.to_datetime(df["날짜"])
    df["연도"] = df["날짜"].dt.year
    return df


df = load_data()

# ── 연평균 기온 계산 ────────────────────────────────────────
yearly = (
    df.groupby("연도")[["평균기온", "최저기온", "최고기온"]]
    .mean()
    .reset_index()
    .sort_values("연도")
)

# 자료가 부실한(관측일수가 너무 적은) 연도는 제외
counts = df.groupby("연도").size()
valid_years = counts[counts >= 300].index
yearly = yearly[yearly["연도"].isin(valid_years)].reset_index(drop=True)

first_year = int(yearly["연도"].min())
last_year = int(yearly["연도"].max())

# ── 화면 상단 ──────────────────────────────────────────────
st.title("🌡️ 서울, 100년 동안 기온은 얼마나 변했을까?")
st.write(
    f"서울 기상 관측 데이터({first_year}년 ~ {last_year}년)를 바탕으로, "
    "해마다 서울의 평균 기온이 어떻게 달라져 왔는지 살펴봅니다."
)

# ── 핵심 지표 ──────────────────────────────────────────────
early_avg = yearly[yearly["연도"] < first_year + 10]["평균기온"].mean()
recent_avg = yearly[yearly["연도"] > last_year - 10]["평균기온"].mean()
diff = recent_avg - early_avg

col1, col2, col3 = st.columns(3)
col1.metric(f"{first_year}년대 초반 평균 기온", f"{early_avg:.1f} ℃")
col2.metric(f"{last_year}년대 최근 평균 기온", f"{recent_avg:.1f} ℃")
col3.metric("기온 변화", f"{diff:+.1f} ℃")

st.divider()

# ── 연평균 기온 추이 그래프 ────────────────────────────────
st.subheader("📈 연평균 기온 변화 추이")

# 추세선 계산 (선형 회귀)
x = yearly["연도"].values
y = yearly["평균기온"].values
coeffs = np.polyfit(x, y, 1)
trend = np.poly1d(coeffs)
trend_per_decade = coeffs[0] * 10

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=yearly["연도"],
        y=yearly["평균기온"],
        mode="lines+markers",
        name="연평균 기온",
        line=dict(color="#4a90d9", width=2),
        marker=dict(size=4),
        hovertemplate="%{x}년<br>평균 기온 %{y:.1f}℃<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=yearly["연도"],
        y=trend(x),
        mode="lines",
        name="추세선(장기 경향)",
        line=dict(color="#e74c3c", width=3, dash="dash"),
        hoverinfo="skip",
    )
)

fig.update_layout(
    xaxis_title="연도",
    yaxis_title="평균 기온 (℃)",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=500,
    margin=dict(l=10, r=10, t=30, b=10),
)

st.plotly_chart(fig, use_container_width=True)

st.info(
    f"📌 추세선을 보면 10년마다 평균적으로 약 **{trend_per_decade:+.2f}℃** 씩 "
    "기온이 변해왔다는 것을 알 수 있어요."
)

st.divider()

# ── 최고·최저 기온도 함께 보기 ────────────────────────────
st.subheader("🔺🔻 연평균 최고·최저 기온도 함께 보기")

fig2 = go.Figure()
fig2.add_trace(
    go.Scatter(
        x=yearly["연도"], y=yearly["최고기온"], mode="lines",
        name="연평균 최고기온", line=dict(color="#e67e22"),
    )
)
fig2.add_trace(
    go.Scatter(
        x=yearly["연도"], y=yearly["평균기온"], mode="lines",
        name="연평균 기온", line=dict(color="#4a90d9"),
    )
)
fig2.add_trace(
    go.Scatter(
        x=yearly["연도"], y=yearly["최저기온"], mode="lines",
        name="연평균 최저기온", line=dict(color="#2980b9"),
    )
)
fig2.update_layout(
    xaxis_title="연도",
    yaxis_title="기온 (℃)",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=450,
    margin=dict(l=10, r=10, t=30, b=10),
)
st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── 일별 평균기온 분포 히스토그램 ─────────────────────────
st.subheader("📊 일별 평균기온은 어느 구간에 몰려 있을까?")
st.write(
    f"{first_year}년부터 {last_year}년까지 서울의 모든 날짜(하루 단위) 평균기온을 "
    "1℃ 구간으로 나누어 얼마나 자주 나타났는지 살펴봅니다."
)

daily_temp = df["평균기온"].dropna()

bin_size = 1
bin_min = int(np.floor(daily_temp.min()))
bin_max = int(np.ceil(daily_temp.max()))

fig3 = go.Figure()
fig3.add_trace(
    go.Histogram(
        x=daily_temp,
        xbins=dict(start=bin_min, end=bin_max, size=bin_size),
        marker=dict(color="#4a90d9", line=dict(color="white", width=0.5)),
        hovertemplate="%{x}℃ 구간<br>%{y}일<extra></extra>",
    )
)

mean_temp = daily_temp.mean()
median_temp = daily_temp.median()

fig3.add_vline(
    x=mean_temp, line=dict(color="#e74c3c", width=2, dash="dash"),
    annotation_text=f"평균 {mean_temp:.1f}℃", annotation_position="top",
)

fig3.update_layout(
    xaxis_title="일별 평균기온 (℃)",
    yaxis_title="날짜 수 (일)",
    bargap=0.02,
    height=450,
    margin=dict(l=10, r=10, t=30, b=10),
)

st.plotly_chart(fig3, use_container_width=True)

hcol1, hcol2, hcol3 = st.columns(3)
hcol1.metric("전체 관측일 수", f"{len(daily_temp):,}일")
hcol2.metric("일별 평균기온의 평균", f"{mean_temp:.1f} ℃")
hcol3.metric("일별 평균기온의 중앙값", f"{median_temp:.1f} ℃")

st.info(
    "📌 막대가 가장 높이 솟은 구간이 서울에서 가장 자주 나타나는 기온대예요. "
    "빨간 점선은 전체 날짜의 평균 기온 위치를 나타냅니다."
)

st.divider()

# ── 최저기온과 최고기온의 관계 산점도 ─────────────────────
st.subheader("🔵 최저기온과 최고기온은 어떤 관계가 있을까?")
st.write(
    "하루하루의 최저기온과 최고기온을 점으로 찍어, 두 값이 함께 움직이는 경향이 "
    "있는지 살펴봅니다."
)

scatter_df = df[["최저기온", "최고기온"]].dropna()

# 상관계수 및 추세선 계산
corr = scatter_df["최저기온"].corr(scatter_df["최고기온"])
sx = scatter_df["최저기온"].values
sy = scatter_df["최고기온"].values
s_coeffs = np.polyfit(sx, sy, 1)
s_trend = np.poly1d(s_coeffs)
x_range = np.linspace(sx.min(), sx.max(), 100)

fig4 = go.Figure()

fig4.add_trace(
    go.Scattergl(
        x=scatter_df["최저기온"],
        y=scatter_df["최고기온"],
        mode="markers",
        name="일별 관측값",
        marker=dict(color="#4a90d9", size=4, opacity=0.25),
        hovertemplate="최저 %{x}℃ / 최고 %{y}℃<extra></extra>",
    )
)

fig4.add_trace(
    go.Scatter(
        x=x_range,
        y=s_trend(x_range),
        mode="lines",
        name="추세선",
        line=dict(color="#e74c3c", width=3, dash="dash"),
        hoverinfo="skip",
    )
)

fig4.update_layout(
    xaxis_title="최저기온 (℃)",
    yaxis_title="최고기온 (℃)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=500,
    margin=dict(l=10, r=10, t=30, b=10),
)

st.plotly_chart(fig4, use_container_width=True)

scol1, scol2 = st.columns(2)
scol1.metric("상관계수", f"{corr:.2f}")
scol2.metric("일교차 평균", f"{(scatter_df['최고기온'] - scatter_df['최저기온']).mean():.1f} ℃")

st.info(
    "📌 점들이 오른쪽 위로 갈수록 촘촘히 올라가는 모양이면, 최저기온이 높은 날은 "
    "최고기온도 높은 경향이 강하다는 뜻이에요. 상관계수가 1에 가까울수록 그 관계가 뚜렷합니다."
)

st.divider()

# ── 원본 데이터 살펴보기 ──────────────────────────────────
with st.expander("📋 연도별 평균 기온 표 보기"):
    show_df = yearly.rename(
        columns={"연도": "연도", "평균기온": "평균기온(℃)", "최저기온": "평균 최저기온(℃)", "최고기온": "평균 최고기온(℃)"}
    ).round(1)
    st.dataframe(show_df, use_container_width=True, hide_index=True)

st.caption("데이터 출처: 기상청 서울 관측소 일별 기온 자료")
