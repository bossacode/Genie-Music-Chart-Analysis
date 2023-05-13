from requests import get
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from collections import deque, defaultdict
from time import sleep


# 노래, 가수 정보 찾는 함수
def find_song_and_artist(dom: BeautifulSoup):
    songs = deque()
    artists = deque()
    for _ in dom.find_all('td', attrs={'class':'subject'}):
        song, artist = _.find_all('p')
        songs.append(song.text)
        artists.append(artist.text)
    return songs, artists


# 스트리밍 횟수 정보 찾는 함수
def find_streaming_info(dom: BeautifulSoup):
    hourly_streamings = deque()
    daily_streamings = deque()
    for hour, day in zip(dom.find_all('td', attrs={'class':'count firstcount'}), dom.find_all('td', attrs={'class':'count secondcount'})):
        hourly_stream = hour.find('p').text.replace(',', '')
        daily_stream = day.find('p').text.replace(',', '')
        hourly_streamings.append(hourly_stream)
        daily_streamings.append(daily_stream)
    return hourly_streamings, daily_streamings


# http response  반환하는 함수
def get_response(url, headers: dict=None, max_count: int=3):
    '''
    headers: http request headers
    max_count: number of iterations when 500 http error happens
    '''
    resp = get(url, headers=headers)
    # 비정상적인 http response 받았을 때
    try:
        resp.raise_for_status()
    except HTTPError as e:
        if 500 <= e.response.status_code < 600: # 500번대 에러 발생 시 10초 쉬고 다시 요청
            if max_count > 0:
                sleep(10)
                get_response(url, headers, max_count-1)
            else:
                print('500번대 에러 재시도 횟수 초과')
                resp= None
        else:
            print(e.response.status_code)
            print(e.response.reason)
            print(e.request.headers)
            resp = None
    return resp


# 가이섬 웹사이트에서 멜론 탑100 정보 스크래핑 하는 함수
def melon_datascraper(url, start_time: str, end_time: str=datetime.now().strftime('%Y-%m-%d %H'), headers:dict =None, max_count: int=3):
    '''
    start_time: date str in format of '%Y-%m-%d %H'     ex.) '2023-1-1 0'
    end_time: date str in format of '%Y-%m-%d %H'       ex.) '2023-1-1 23'
    headers: http request headers
    max_count: number of iterations when 500 http error happens
    '''
    start = datetime.strptime(start_time, '%Y-%m-%d %H')
    end = datetime.strptime(end_time, '%Y-%m-%d %H')
    diff = end - start
    
    # end_time이 start_time보다 빠른 경우
    if diff.days < 0:
        print('start time must be before end time')
        return None
    
    record = defaultdict(deque)
    while start <= end:
        while start.hour in range(1,8): # 새벽 1시부터 아침 7시까지는 이용자수 데이터가 존재 하지 않아서 skip
            start += timedelta(hours=1)
        
        new_url = url + '/' + start.strftime('%Y%m%d/%H')    # url 형태가 https://xn--o39an51b2re.com/melon/chart/top100/20230228/01
        resp = get_response(new_url, headers, max_count)

        # http 에러난 경우
        if resp == None:
            print(f'에러 발생 시점: {start}')
            break

        dom = BeautifulSoup(resp.text, 'html.parser')
        songs, artists = find_song_and_artist(dom)
        hourly_streamings, daily_streamings = find_streaming_info(dom)    

        for s, a, h, d in zip(songs, artists, hourly_streamings, daily_streamings):
            record['song'].append(s)
            record['artist'].append(a)
            record['day'].append(start.strftime('%Y-%m-%d'))
            record['hour'].append(int(start.strftime('%H')))
            record['1h streaming'].append(h)
            record['24h streaming'].append(d)

        start += timedelta(hours=1)
    return record