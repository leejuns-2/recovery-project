# import pandas as pd

# weather = pd.read_parquet("data/processed/weather_daily.parquet")

# # 비 안 온 날 결측값 → 0으로 채우기
# weather["일강수량"] = weather["일강수량"].fillna(0)
# weather["1시간최다강수"] = weather["1시간최다강수"].fillna(0)

# # 확인
# print("결측값 처리 후:")
# print(weather.isnull().sum())
# print()

# # 호우 기준 확인 — 일강수량 80mm 이상인 날
# heavy_rain = weather[weather["일강수량"] >= 80]
# print(f"일강수량 80mm 이상인 날: {len(heavy_rain)}일")
# print(heavy_rain[["날짜", "일강수량", "1시간최다강수"]])

# # 저장
# weather.to_parquet("data/processed/weather_daily.parquet", index=False)
# print("\n저장 완료")

import pandas as pd

aws = pd.read_csv(
    "data/raw/weather/OBS_AWS_DD_20260419170121.csv",
    encoding="cp949",
    usecols=["지점", "지점명", "일시", "일강수량(mm)"]
)

aws = aws.rename(columns={
    "일시": "날짜",
    "일강수량(mm)": "일강수량"
})

aws["날짜"] = pd.to_datetime(aws["날짜"])
aws["일강수량"] = aws["일강수량"].fillna(0)

# 호우 기준별 이벤트 수 확인
print("--- 기준별 호우 발생 현황 ---")
for mm in [80, 60, 50, 40, 30]:
    n = aws[aws["일강수량"] >= mm]
    print(f"{mm}mm 이상: {n['날짜'].nunique()}일, {n['지점명'].nunique()}개 지점")

aws.to_parquet("data/processed/aws_daily.parquet", index=False)
print("\n저장 완료: data/processed/aws_daily.parquet")