from datetime import datetime, timedelta
import numpy as np


def data_cleaner(df):
    '''
    df is a pandas Dataframe that has the following columns

    datetime: str in form of "%Y-%m-%d %H"
    cumulative_listeners: int
    cumulative_listeners: int
    '''
    
    # date, hour 열 만들기
    df['datetime'] = df['datetime'].map(lambda x: datetime.strptime(x, '%Y-%m-%d %H'))
    df['date'] = df['datetime'].dt.date
    df['hour'] = df['datetime'].dt.hour

    # 인접하는 row 간에 시간차 구하기 (1시간 차이가 나는 row만 현재 누적값에서 이전 누적값을 빼서 실시간 정보를 얻을 수 있다)
    df['time_diff'] = df['datetime'] - df['datetime'].shift(1)

    # 실시간 스트리밍 정보 구하기 (실시간 정보 구할 수 없으면 결측 처리)
    df['current_streams'] = np.where(df['time_diff'] == timedelta(hours=1),
                                    df['cumulative_streams'] - df['cumulative_streams'].shift(1),
                                    np.nan)
    
    # 필요 없는 row, column 버리고 index 새로 설정
    df.dropna(inplace=True)
    df.drop(['datetime', 'cumulative_listeners', 'cumulative_streams', 'time_diff'], axis=1, inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df