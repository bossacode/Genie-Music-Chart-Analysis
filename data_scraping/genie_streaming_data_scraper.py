from requests import get
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from collections import deque, defaultdict

# from requests.exceptions import HTTPError
# from time import sleep


# 노래, 가수, 누적 청취자수, 누적 재생수 정보 찾는 함수
def find_info(dom: BeautifulSoup):
    songs_artists = deque()
    listeners = deque()
    streams = deque()

    song_artist_info = dom.find_all('td', attrs={'class':'subject'})
    listener_info = dom.find_all('td', attrs={'class':'count firstcount'})
    stream_info = dom.find_all('td', attrs={'class':'count secondcount'})

    if song_artist_info:    # 페이지에 해당 정보들이 존재하는 경우
        for s_a, l, s in zip(song_artist_info, listener_info, stream_info):
            
            song, artist = s_a.find_all('p')
            cum_listener = l.find('p').text.replace(',', '')
            cum_stream = s.find('p').text.replace(',', '')

            songs_artists.append(song.text + '_' + artist.text)
            listeners.append(cum_listener)
            streams.append(cum_stream)
        return songs_artists, listeners, streams
    else:                   # 페이지에 해당 정보들이 존재하지 않는 경우
        return None, None, None


# http response  반환하는 함수
def get_response(url, headers: dict=None, max_count: int=3):
    '''
    headers: http request headers
    max_count: number of iterations when 500 http error happens
    '''
    resp = get(url, headers=headers)

    # try:
    #     resp.raise_for_status()     # 비정상적인 http response 받았을 때 예외 처리
    # except HTTPError as e:
    #     if 500 <= e.response.status_code < 600: # 500번대 에러 발생 시 5초 쉬고 다시 요청
    #         if max_count > 0:
    #             sleep(5)
    #             get_response(url, headers, max_count-1)
    #         else:
    #             print('500번대 에러 재시도 횟수 초과')
    #             resp= None
    #     else:
    #         print(e.response.status_code)
    #         print(e.response.reason)
    #         print(e.request.headers)
    #         resp = None
    return resp


# 가이섬 웹사이트에서 지니 실시간 차트 정보 스크래핑 하는 함수
def genie_datascraper(url, start_time: str, end_time: str=datetime.now().strftime('%Y-%m-%d %H'), headers:dict =None, max_count: int=3) -> defaultdict:
    '''
    start_time: date str in format of '%Y-%m-%d %H'     ex.) '2023-1-1 0'
    end_time: date str in format of '%Y-%m-%d %H'       ex.) '2023-1-1 23'
    headers: http request headers
    max_count: number of iterations when 500 http error happens
    '''
    start = datetime.strptime(start_time, '%Y-%m-%d %H')
    end = datetime.strptime(end_time, '%Y-%m-%d %H')
    diff = end - start
    
    if diff.days < 0:   # end_time이 start_time보다 빠른 경우
        print('start time must be before end time')
        return None
    
    record = defaultdict(list)
    while start <= end:
        if start.day == 1 and start.hour == 0:  # 진행상황 트래킹 (매 달 시작할 때 메세지 출력)
            print(f'{start} 시작')
    
        new_url = url + '/' + start.strftime('%Y%m%d/%H')    # url 형태가 https://xn--o39an51b2re.com/genie/chart/realtime/20230228/01
        resp = get_response(new_url, headers, max_count)

        # if resp == None:    # http 에러난 경우
        #     print(f'에러 발생 시점: {start}')
        #     break

        dom = BeautifulSoup(resp.text, 'html.parser')
        songs_artists, listeners, streams = find_info(dom)

        if songs_artists == None:   # 페이지에 정보가 존재하지 않는 경우
            print('-' * 50)
            print(f'{start}에 해당하는 페이지에는 음원 정보가 없음')
            print('-' * 50)
            start += timedelta(hours=1)
            continue

        for s_a, l, s in zip(songs_artists, listeners, streams):
            try:
                l = int(l); s = int(s)  # 결측값이어서 '-' 있는 경우 정수 변환 불가하므로 예외 처리
            except ValueError:
                print(f'!!!결측값 발생!!! {start} {s_a}')
                continue
            
            record[s_a].append(
                    {
                        'datetime' : start.strftime('%Y-%m-%d %H'),
                        'cumulative_listeners' : l,
                        'cumulative_streams' : s
                    })
        
        start += timedelta(hours=1)
    return record