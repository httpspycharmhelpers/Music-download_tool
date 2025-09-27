import urllib.request
import urllib.parse
import json
import time
import os
import socket
import re
import random
import string
import sys
import subprocess
import threading
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# 设置超时时间（秒）
REQUEST_TIMEOUT = 15
socket.setdefaulttimeout(REQUEST_TIMEOUT)

# 全局下载目录
DOWNLOAD_DIR = "music_downloads"
# 下载记录文件
DOWNLOAD_HISTORY_FILE = "Download_Log.csv"

# 短剧下载目录
SHORT_DRAMA_DIR = "short_dramas"
# 短剧下载记录文件
SHORT_DRAMA_HISTORY_FILE = "Short_Drama_Log.csv"

def create_download_dir():
    """创建下载目录（如果不存在）"""
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        print(f"已创建下载目录: {os.path.abspath(DOWNLOAD_DIR)}")
    return DOWNLOAD_DIR

def init_download_history():
    """初始化下载记录文件"""
    if not os.path.exists(DOWNLOAD_HISTORY_FILE):
        with open(DOWNLOAD_HISTORY_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['时间', '歌曲名称', '歌手', '平台', '文件路径'])

def save_download_history(song_name, singer, platform, file_path):
    """保存下载记录"""
    try:
        init_download_history()
        with open(DOWNLOAD_HISTORY_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                song_name,
                singer,
                platform,
                file_path
            ])
        print(f"下载记录已保存")
    except Exception as e:
        print(f"保存下载记录失败: {str(e)}")

def show_download_history():
    """显示下载历史记录"""
    try:
        if not os.path.exists(DOWNLOAD_HISTORY_FILE):
            print("暂无下载记录")
            return
        
        with open(DOWNLOAD_HISTORY_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            if len(rows) <= 1:
                print("暂无下载记录")
                return
            
            print("\n===== 下载历史记录 =====")
            for i, row in enumerate(rows[1:], 1):  # 跳过标题行
                print(f"{i}. {row[0]} - [{row[3]}] {row[1]} - {row[2]}")
            
            print(f"\n共 {len(rows)-1} 条下载记录")
    except Exception as e:
        print(f"读取下载记录失败: {str(e)}")

def search_songs(keyword, page_size=500):
    """搜索歌曲 - 增加超时和错误处理"""
    encoded_keyword = urllib.parse.quote(keyword)
    url = f'https://c.musicapp.migu.cn/v1.0/content/search_all.do?text={encoded_keyword}&pageNo=1&pageSize={page_size}&isCopyright=1&sort=1&searchSwitch=%7B%22song%22%3A1%2C%22album%22%3A0%2C%22singer%22%3A0%2C%22tagSong%22%3A1%2C%22mvSong%22%3A0%2C%22bestShow%22%3A1%7D'
    
    try:
        req = urllib.request.Request(url, headers={'channel': '0140210'})
        res = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
        data = json.load(res)
        
        if 'songResultData' in data and 'result' in data['songResultData']:
            return data['songResultData']['result']
        print("API返回数据结构异常")
        return []
    except urllib.error.URLError as e:
        print(f"网络请求失败: {e.reason}")
    except urllib.error.HTTPError as e:
        print(f"HTTP错误: {e.code} - {e.reason}")
    except socket.timeout:
        print("请求超时，请稍后再试")
    except json.JSONDecodeError:
        print("API返回数据解析失败")
    except Exception as e:
        print(f"搜索过程中发生错误: {type(e).__name__} - {str(e)}")
    return []

def display_song_list(song_list, title="歌曲列表"):
    """显示歌曲列表 - 增加健壮性检查"""
    if not song_list:
        print("未找到歌曲")
        return []
    
    print(f"\n===== {title} =====")
    total_list = []
    count = 1
    
    for song_data in song_list:
        try:
            song_name = song_data.get('name', '未知歌曲')
            singers = song_data.get('singers', [{}])[0].get('name', '未知歌手')
            contentId = song_data.get('contentId', '')
            copyrightId = song_data.get('copyrightId', '')
            
            if not contentId or not copyrightId:
                continue
                
            album_info = song_data.get('albums', [{}])[0] if song_data.get('albums') else {}
            albumId = album_info.get('id', '0')
            albums_name = album_info.get('name', '未知专辑')
            
            list_data = [count, song_name, singers, albums_name, contentId, copyrightId, albumId]
            count += 1
            total_list.append(list_data)
            print(f"{list_data[0]}. {list_data[1]} - {list_data[2]}")
        except Exception as e:
            print(f"处理歌曲数据时出错: {type(e).__name__} - {str(e)}")
            continue
    
    print(f"共找到 {len(total_list)} 首有效歌曲")
    return total_list

def download_song(song):
    """下载选中的歌曲 - 增加超时、目录支持和错误处理"""
    try:
        song_name = song[1]
        singers = song[2]
        contentId = song[4]
        copyrightId = song[5]
        albumId = song[6]
        
        print(f"开始下载: {song_name} - {singers}")
        
        url = f'https://c.musicapp.migu.cn/MIGUM3.0/strategy/listen-url/v2.3?copyrightId={copyrightId}&contentId={contentId}&resourceType=2&albumId={albumId}&netType=01&toneFlag=PQ'
        req = urllib.request.Request(url, headers={
            'channel': '0140210',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        try:
            res = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
            data = json.load(res)
            
            if not data.get('data') or not data['data'].get('url'):
                print("获取下载链接失败: API返回无效数据")
                return False
                
            down_url = data['data']['url']
        except Exception as e:
            print(f"获取下载链接失败: {type(e).__name__} - {str(e)}")
            return False
        
        try:
            res1 = urllib.request.urlopen(down_url, timeout=REQUEST_TIMEOUT)
            
            content_length = res1.headers.get('Content-Length')
            total_size = int(content_length) if content_length else 0
            downloaded = 0
            chunk_size = 1024 * 8
            
            download_dir = create_download_dir()
            
            filename = f'{song_name}-{singers}.mp3'
            for char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
                filename = filename.replace(char, '_')
            
            # 处理文件名编码问题
            try:
                filename = filename.encode('utf-8').decode('utf-8')
            except UnicodeEncodeError:
                filename = 'song.wav'
            
            filepath = os.path.join(download_dir, filename)
            
            with open(filepath, 'wb') as f:
                while True:
                    try:
                        chunk = res1.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            percent = min(100, int(100 * downloaded / total_size))
                            # 计算下载速度和剩余时间
                            elapsed_time = time.time() - start_time if 'start_time' in locals() else 0
                            if elapsed_time > 0:
                                speed = downloaded / elapsed_time / 1024  # KB/s
                                remaining = (total_size - downloaded) / (speed * 1024) if speed > 0 else 0
                                eta_min = int(remaining // 60)
                                eta_sec = int(remaining % 60)
                                eta_str = f"{eta_min}:{eta_sec:02d}"
                            else:
                                speed = 0
                                eta_str = "0:00"
                            
                            # 格式化下载大小显示
                            downloaded_mb = downloaded / (1024 * 1024)
                            total_mb = total_size / (1024 * 1024)
                            
                            # 显示进度信息 - 修改为图片中的格式
                            print(f"\rMusic downloading........ {downloaded_mb:.1f}/{total_mb:.1f} MB {speed:.1f} kB/s eta {eta_str}", end='')
                        else:
                            print(f"\r已下载: {downloaded} kib", end='')
                    except socket.timeout:
                        print("\n下载超时，继续尝试...")
                        continue
            
            print('\n下载完成!')
            print(f"歌曲已保存至: {os.path.abspath(filepath)}")
            
            # 保存下载记录
            save_download_history(song_name, singers, "咪咕音乐", filepath)
            return True
        except Exception as e:
            print(f"下载失败: {type(e).__name__} - {str(e)}")
            return False
    except Exception as e:
        print(f"下载过程中发生错误: {type(e).__name__} - {str(e)}")
        return False

# ============================= 酷狗音乐支持 =============================
def search_kugou(keyword):
    """搜索酷狗音乐 - 使用稳定可靠的API"""
    try:
        encoded_keyword = urllib.parse.quote(keyword)
        # 使用经过验证的API
        url = f"https://songsearch.kugou.com/song_search_v2?keyword={encoded_keyword}&page=1&pagesize=20"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.kugou.com/',
            'Cookie': 'kg_mid=' + ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        }
        
        req = urllib.request.Request(url, headers=headers)
        res = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
        data = json.load(res)
        
        if data.get('status') == 1 and data.get('data') and data['data'].get('lists'):
            return data['data']['lists']
        print("酷狗API返回数据异常")
        return []
    except Exception as e:
        print(f"酷狗搜索失败: {type(e).__name__} - {str(e)}")
        return []

def display_kugou_list(song_list, title="酷狗搜索结果"):
    """显示酷狗音乐列表"""
    if not song_list:
        print("酷狗未找到相关歌曲")
        return []
    
    print(f"\n===== {title} =====")
    total_list = []
    
    for idx, song in enumerate(song_list, 1):
        try:
            song_name = song.get('SongName', '未知歌曲')
            singers = song.get('SingerName', '未知歌手')
            file_hash = song.get('FileHash', '')
            album_id = song.get('AlbumID', '')
            
            if not file_hash:
                continue
                
            total_list.append([idx, song_name, singers, file_hash, album_id])
            print(f"{idx}. {song_name} - {singers}")
        except Exception as e:
            print(f"处理酷狗歌曲数据时出错: {str(e)}")
            continue
    
    print(f"共找到 {len(total_list)} 首歌曲")
    return total_list

def download_kugou(song):
    """下载酷狗音乐 - 使用稳定可靠的API"""
    try:
        song_name = song[1]
        singers = song[2]
        file_hash = song[3]
        album_id = song[4]
        
        print(f"开始下载酷狗音乐: {song_name} - {singers}")
        
        # 使用经过验证的API
        url = f"https://wwwapi.kugou.com/yy/index.php?r=play/getdata&hash={file_hash}&album_id={album_id}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.kugou.com/',
            'Cookie': 'kg_mid=' + ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        }
        
        req = urllib.request.Request(url, headers=headers)
        res = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
        data = json.load(res)
        
        if data.get('err_code') != 0 or not data.get('data') or not data['data'].get('play_url'):
            print("获取酷狗下载链接失败")
            return False
        
        down_url = data['data']['play_url']
        
        # 验证下载链接
        if not down_url.startswith('http'):
            print("酷狗下载链接无效")
            return False
            
        success, filepath = download_file(down_url, song_name, singers, "mp3")
        if success:
            # 保存下载记录
            save_download_history(song_name, singers, "酷狗音乐", filepath)
        return success
    except Exception as e:
        print(f"酷狗下载失败: {type(e).__name__} - {str(e)}")
        return False

# ============================= QQ音乐支持 =============================
def search_qq(keyword):
    """搜索QQ音乐 - 使用稳定可靠的API"""
    try:
        encoded_keyword = urllib.parse.quote(keyword)
        # 使用经过验证的API
        url = f"https://c.y.qq.com/soso/fcgi-bin/client_search_cp?p=1&n=20&w={encoded_keyword}&format=json"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://y.qq.com/'
        }
        
        req = urllib.request.Request(url, headers=headers)
        res = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
        raw_data = res.read().decode('utf-8')
        
        # 处理JSON响应
        if raw_data.startswith('callback(') and raw_data.endswith(')'):
            json_str = raw_data[9:-1]
            data = json.loads(json_str)
        else:
            data = json.loads(raw_data)
        
        if data.get('code') == 0 and data.get('data') and data['data'].get('song') and data['data']['song'].get('list'):
            return data['data']['song']['list']
        print("QQ音乐未找到相关歌曲")
        return []
    except Exception as e:
        print(f"QQ音乐搜索失败: {type(e).__name__} - {str(e)}")
        return []

def display_qq_list(song_list, title="QQ音乐搜索结果"):
    """显示QQ音乐列表"""
    if not song_list:
        print("QQ音乐未找到相关歌曲")
        return []
    
    print(f"\n===== {title} =====")
    total_list = []
    
    for idx, song in enumerate(song_list, 1):
        try:
            song_name = song.get('songname', '未知歌曲')
            singers = '、'.join([s['name'] for s in song.get('singer', [])]) or '未知歌手'
            song_mid = song.get('songmid', '')
            
            if not song_mid:
                continue
                
            total_list.append([idx, song_name, singers, song_mid])
            print(f"{idx}. {song_name} - {singers}")
        except Exception as e:
            print(f"处理QQ音乐歌曲数据时出错: {str(e)}")
            continue
    
    print(f"共找到 {len(total_list)} 首歌曲")
    return total_list

def download_qq(song):
    """下载QQ音乐 - 使用稳定可靠的API"""
    try:
        s_name = song[1]
        singers = song[2]
        song_mid = song[3]
        
        print(f"开始下载QQ音乐: {s_name} - {singers}")
        
        # 使用经过验证的API
        url = f"https://u.y.qq.com/cgi-bin/musicu.fcg?format=json&data=%7B%22req_0%22%3A%7B%22module%22%3A%22vkey.GetVkeyServer%22%2C%22method%22%3A%22CgiGetVkey%22%2C%22param%22%3A%7B%22guid%22%3A%22358840384%22%2C%22songmid%22%3A%5B%22{song_mid}%22%5D%2C%22songtype%22%3A%5B0%5D%2C%22uin%22%3A%221443481947%22%2C%22loginflag%22%3A1%2C%22platform%22%3A%2220%22%7D%7D%2C%22comm%22%3A%7B%22uin%22%3A%2218585073516%22%2C%22format%22%3A%22json%22%2C%22ct%22%3A24%2C%22cv%22%3A0%7D%7D"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://y.qq.com/'
        }
        
        req = urllib.request.Request(url, headers=headers)
        res = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
        data = json.load(res)
        
        # 解析API响应
        try:
            purl = data['req_0']['data']['midurlinfo'][0]['purl']
            if not purl:
                print("获取QQ音乐下载链接失败")
                return False
            
            down_url = f"https://dl.stream.qqmusic.qq.com/{purl}"
            success, filepath = download_file(down_url, s_name, singers, "m4a")
            if success:
                # 保存下载记录
                save_download_history(s_name, singers, "QQ音乐", filepath)
            return success
        except (KeyError, IndexError):
            print("解析QQ音乐下载链接失败")
            return False
    except Exception as e:
        print(f"QQ音乐下载失败: {type(e).__name__} - {str(e)}")
        return False

# ============================= 网易云音乐支持 =============================
def search_cloud(keyword):
    """搜索网易云音乐 - 使用稳定可靠的API"""
    try:
        encoded_keyword = urllib.parse.quote(keyword)
        # 使用经过验证的API
        url = f"https://music.163.com/api/cloudsearch/pc?s={encoded_keyword}&type=1&offset=0&limit=20"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://music.163.com/'
        }
        
        req = urllib.request.Request(url, headers=headers)
        res = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
        data = json.load(res)
        
        if data.get('code') == 200 and data.get('result') and data['result'].get('songs'):
            return data['result']['songs']
        print("网易云音乐未找到相关歌曲")
        return []
    except Exception as e:
        print(f"网易云音乐搜索失败: {type(e).__name__} - {str(e)}")
        return []

def display_cloud_list(song_list, title="网易云音乐搜索结果"):
    """显示网易云音乐列表"""
    if not song_list:
        print("网易云音乐未找到相关歌曲")
        return []
    
    print(f"\n===== {title} =====")
    total_list = []
    
    for idx, song in enumerate(song_list, 1):
        try:
            s_name = song.get('name', '未知歌曲')
            singers = '、'.join([s['name'] for s in song.get('ar', [])]) or '未知歌手'
            song_id = song.get('id', '')
            
            if not song_id:
                continue
                
            total_list.append([idx, s_name, singers, song_id])
            print(f"{idx}. {s_name} - {singers}")
        except Exception as e:
            print(f"处理网易云音乐歌曲数据时出错: {str(e)}")
            continue
    
    print(f"共找到 {len(total_list)} 首歌曲")
    return total_list

def download_cloud(song):
    """下载网易云音乐 - 使用稳定可靠的API"""
    try:
        s_name = song[1]
        singers = song[2]
        song_id = song[3]
        
        print(f"开始下载网易云音乐: {s_name} - {singers}")
        
        # 使用经过验证的API
        url = f"https://music.163.com/api/song/enhance/player/url?id={song_id}&ids=%5B{song_id}%5D&br=320000"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': f'https://music.163.com/song?id={song_id}'
        }
        
        req = urllib.request.Request(url, headers=headers)
        res = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
        data = json.load(res)
        
        if data.get('code') != 200 or not data.get('data') or not data['data'][0].get('url'):
            print("获取网易云音乐下载链接失败")
            return False
            
        down_url = data['data'][0]['url']
        success, filepath = download_file(down_url, s_name, singers, "mp3")
        if success:
            # 保存下载记录
            save_download_history(s_name, singers, "网易云音乐", filepath)
        return success
    except Exception as e:
        print(f"网易云音乐下载失败: {type(e).__name__} - {str(e)}")
        return False

# ============================= 通用下载函数 =============================
def download_file(url, title, creator, ext):
    """通用文件下载函数 - 增强稳定性和错误处理"""
    try:
        # 处理URL编码问题
        url = urllib.parse.unquote(url)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.google.com/',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        }
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as res:
            # 检查HTTP状态码
            if res.status != 200:
                print(f"下载失败: HTTP状态码 {res.status}")
                return False, None
                
            # 检查内容类型
            content_type = res.headers.get('Content-Type', '')
            if 'html' in content_type or 'text' in content_type:
                print("下载链接无效，返回了HTML内容")
                return False, None
                
            content_length = res.headers.get('Content-Length')
            total_size = int(content_length) if content_length else 0
            downloaded = 0
            chunk_size = 1024 * 8
            
            download_dir = create_download_dir()
            
            # 清理文件名中的非法字符
            filename = f'{title}-{creator}.{ext}'
            invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
            for char in invalid_chars:
                filename = filename.replace(char, '_')
            
            # 缩短过长的文件名
            if len(filename) > 100:
                filename = filename[:50] + filename[-50:]
            
            filepath = os.path.join(download_dir, filename)
            
            start_time = time.time()
            with open(filepath, 'wb') as f:
                while True:
                    try:
                        chunk = res.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            # 计算下载速度和剩余时间
                            elapsed_time = time.time() - start_time
                            if elapsed_time > 0:
                                speed = downloaded / elapsed_time / 1024  # KB/s
                                remaining = (total_size - downloaded) / (speed * 1024) if speed > 0 else 0
                                eta_min = int(remaining // 60)
                                eta_sec = int(remaining % 60)
                                eta_str = f"{eta_min}:{eta_sec:02d}"
                            else:
                                speed = 0
                                eta_str = "0:00"
                            
                            # 格式化下载大小显示
                            downloaded_mb = downloaded / (1024 * 1024)
                            total_mb = total_size / (1024 * 1024)
                            
                            # 显示进度信息 - 修改为图片中的格式
                            print(f"\rMusic downloading........ {downloaded_mb:.1f}/{total_mb:.1f} MB {speed:.1f} kB/s eta {eta_str}", end='')
                        else:
                            print(f"\r已下载: {downloaded} 字节", end='')
                    except socket.timeout:
                        print("\n下载超时，继续尝试...")
                        continue
            
            print('\n下载完成!')
            return True, filepath
    except urllib.error.HTTPError as e:
        print(f"HTTP错误: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        print(f"URL错误: {e.reason}")
    except socket.timeout:
        print("下载超时")
    except Exception as e:
        print(f"下载失败: {type(e).__name__} - {str(e)}")
    return False, None

# ============================= 全网搜索功能 =============================
def search_all_platforms(keyword, max_results=10):
    """全网搜索 - 同时搜索所有平台"""
    print(f"正在全网搜索: {keyword}")
    
    # 存储所有平台的结果
    all_results = []
    
    # 定义搜索函数列表
    search_functions = [
        ("咪咕音乐", search_songs),
        ("酷狗音乐", search_kugou),
        ("QQ音乐", search_qq),
        ("网易云音乐", search_cloud)
    ]
    
    # 使用线程池并发搜索
    with ThreadPoolExecutor(max_workers=4) as executor:
        # 提交所有搜索任务
        future_to_platform = {
            executor.submit(search_func, keyword): (platform_name, search_func) 
            for platform_name, search_func in search_functions
        }
        
        # 处理搜索结果
        for future in as_completed(future_to_platform):
            platform_name, search_func = future_to_platform[future]
            try:
                results = future.result()
                if results:
                    print(f"{platform_name}找到 {len(results)} 个结果")
                    # 为每个结果添加平台标识
                    for result in results[:max_results]:
                        # 创建一个包含平台信息的字典
                        result_with_platform = {
                            'platform': platform_name,
                            'data': result
                        }
                        all_results.append(result_with_platform)
                else:
                    print(f"{platform_name}未找到结果")
            except Exception as e:
                print(f"{platform_name}搜索出错: {str(e)}")
    
    return all_results

def display_all_platforms_results(results, title="全网搜索结果"):
    """显示全网搜索结果"""
    if not results:
        print("全网搜索未找到相关歌曲")
        return []
    
    print(f"\n===== {title} =====")
    total_list = []
    
    for idx, result in enumerate(results, 1):
        try:
            platform = result['platform']
            data = result['data']
            
            # 根据不同平台解析数据
            if platform == "咪咕音乐":
                s_name = data.get('name', '未知歌曲')
                singers = data.get('singers', [{}])[0].get('name', '未知歌手')
                contentId = data.get('contentId', '')
                copyrightId = data.get('copyrightId', '')
                album_info = data.get('albums', [{}])[0] if data.get('albums') else {}
                albumId = album_info.get('id', '0')
                
                if not contentId or not copyrightId:
                    continue
                    
                total_list.append([idx, s_name, singers, contentId, copyrightId, albumId, platform])
                print(f"{idx}. [{platform}] {s_name} - {singers}")
                
            elif platform == "酷狗音乐":
                s_name = data.get('SongName', '未知歌曲')
                singers = data.get('SingerName', '未知歌手')
                file_hash = data.get('FileHash', '')
                album_id = data.get('AlbumID', '')
                
                if not file_hash:
                    continue
                    
                total_list.append([idx, s_name, singers, file_hash, album_id, '', platform])
                print(f"{idx}. [{platform}] {s_name} - {singers}")
                
            elif platform == "QQ音乐":
                s_name = data.get('songname', '未知歌曲')
                singers = '、'.join([s['name'] for s in data.get('singer', [])]) or '未知歌手'
                song_mid = data.get('songmid', '')
                
                if not song_mid:
                    continue
                    
                total_list.append([idx, s_name, singers, song_mid, '', '', platform])
                print(f"{idx}. [{platform}] {s_name} - {singers}")
                
            elif platform == "网易云音乐":
                s_name = data.get('name', '未知歌曲')
                singers = '、'.join([s['name'] for s in data.get('ar', [])]) or '未知歌手'
                song_id = data.get('id', '')
                
                if not song_id:
                    continue
                    
                total_list.append([idx, s_name, singers, song_id, '', '', platform])
                print(f"{idx}. [{platform}] {s_name} - {singers}")
                
        except Exception as e:
            print(f"处理全网搜索结果时出错: {str(e)}")
            continue
    
    print(f"全网共找到 {len(total_list)} 首歌曲")
    return total_list

def download_from_all_platforms(song):
    """从全网搜索结果中下载歌曲"""
    try:
        platform = song[6]  # 平台信息在第七个元素
        
        if platform == "咪咕音乐":
            # 咪咕需要特殊处理，因为它需要更多参数
            contentId = song[3]
            copyrightId = song[4]
            albumId = song[5]
            s_name = song[1]
            singers = song[2]
            
            print(f"开始下载咪咕音乐: {s_name} - {singers}")
            
            url = f'https://c.musicapp.migu.cn/MIGUM3.0/strategy/listen-url/v2.3?copyrightId={copyrightId}&contentId={contentId}&resourceType=2&albumId={albumId}&netType=01&toneFlag=PQ'
            req = urllib.request.Request(url, headers={
                'channel': '0140210',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            res = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
            data = json.load(res)
            
            if not data.get('data') or not data['data'].get('url'):
                print("获取咪咕下载链接失败")
                return False
                
            down_url = data['data']['url']
            success, filepath = download_file(down_url, s_name, singers, "mp3")
            if success:
                # 保存下载记录
                save_download_history(s_name, singers, "咪咕音乐", filepath)
            return success
            
        elif platform == "酷狗音乐":
            # 调用酷狗下载函数
            return download_kugou(song)
            
        elif platform == "QQ音乐":
            # 调用QQ音乐下载函数
            return download_qq(song)
            
        elif platform == "网易云音乐":
            # 调用网易云音乐下载函数
            return download_cloud(song)
            
    except Exception as e:
        print(f"全网下载失败: {type(e).__name__} - {str(e)}")
        return False

# ============================= 短剧功能 =============================
def create_short_drama_dir():
    """创建短剧下载目录（如果不存在）"""
    if not os.path.exists(SHORT_DRAMA_DIR):
        os.makedirs(SHORT_DRAMA_DIR)
        print(f"已创建短剧下载目录: {os.path.abspath(SHORT_DRAMA_DIR)}")
    return SHORT_DRAMA_DIR

def init_short_drama_history():
    """初始化短剧下载记录文件"""
    if not os.path.exists(SHORT_DRAMA_HISTORY_FILE):
        with open(SHORT_DRAMA_HISTORY_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['时间', '短剧名称', '集数', '平台', '文件路径'])

def save_short_drama_history(drama_name, episode, platform, file_path):
    """保存短剧下载记录"""
    try:
        init_short_drama_history()
        with open(SHORT_DRAMA_HISTORY_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                drama_name,
                episode,
                platform,
                file_path
            ])
        print(f"短剧下载记录已保存")
    except Exception as e:
        print(f"保存短剧下载记录失败: {str(e)}")

def show_short_drama_history():
    """显示短剧下载历史记录"""
    try:
        if not os.path.exists(SHORT_DRAMA_HISTORY_FILE):
            print("暂无短剧下载记录")
            return
        
        with open(SHORT_DRAMA_HISTORY_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            if len(rows) <= 1:
                print("暂无短剧下载记录")
                return
            
            print("\n===== 短剧下载历史记录 =====")
            for i, row in enumerate(rows[1:], 1):  # 跳过标题行
                print(f"{i}. {row[0]} - [{row[3]}] {row[1]} 第{row[2]}集")
            
            print(f"\n共 {len(rows)-1} 条短剧下载记录")
    except Exception as e:
        print(f"读取短剧下载记录失败: {str(e)}")

def search_short_drama(keyword):
    """搜索短剧 - 使用即刻短剧API"""
    try:
        encoded_keyword = urllib.parse.quote(keyword)
        url = f"https://api.uuuka.com/v1/short_drama/search?keyword={encoded_keyword}&page=1&limit=20"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json'
        }
        
        req = urllib.request.Request(url, headers=headers)
        res = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
        data = json.load(res)
        
        if data.get('code') == 200 and data.get('data') and data['data'].get('list'):
            return data['data']['list']
        print("短剧API返回数据异常")
        return []
    except Exception as e:
        print(f"短剧搜索失败: {type(e).__name__} - {str(e)}")
        return []

def display_short_drama_list(drama_list, title="短剧搜索结果"):
    """显示短剧列表"""
    if not drama_list:
        print("未找到短剧")
        return []
    
    print(f"\n===== {title} =====")
    total_list = []
    
    for idx, drama in enumerate(drama_list, 1):
        try:
            drama_name = drama.get('name', '未知短剧')
            actor = drama.get('actor', '未知演员')
            total_episodes = drama.get('total_episodes', 0)
            drama_id = drama.get('id', '')
            
            if not drama_id:
                continue
                
            total_list.append([idx, drama_name, actor, total_episodes, drama_id])
            print(f"{idx}. {drama_name} - {actor} (共{total_episodes}集)")
        except Exception as e:
            print(f"处理短剧数据时出错: {str(e)}")
            continue
    
    print(f"共找到 {len(total_list)} 部短剧")
    return total_list

def get_drama_episodes(drama_id):
    """获取短剧的剧集列表"""
    try:
        url = f"https://api.uuuka.com/v1/short_drama/{drama_id}/episodes"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json'
        }
        
        req = urllib.request.Request(url, headers=headers)
        res = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
        data = json.load(res)
        
        if data.get('code') == 200 and data.get('data'):
            return data['data']
        print("获取剧集列表失败")
        return []
    except Exception as e:
        print(f"获取剧集列表失败: {type(e).__name__} - {str(e)}")
        return []

def display_episode_list(episode_list, drama_name, title="剧集列表"):
    """显示剧集列表"""
    if not episode_list:
        print("未找到剧集")
        return []
    
    print(f"\n===== {drama_name} - {title} =====")
    total_list = []
    
    for idx, episode in enumerate(episode_list, 1):
        try:
            episode_num = episode.get('episode_num', 0)
            episode_title = episode.get('title', f'第{episode_num}集')
            episode_id = episode.get('id', '')
            duration = episode.get('duration', '未知时长')
            
            if not episode_id:
                continue
                
            total_list.append([idx, episode_num, episode_title, episode_id, duration])
            print(f"{idx}. 第{episode_num}集 - {episode_title} ({duration})")
        except Exception as e:
            print(f"处理剧集数据时出错: {str(e)}")
            continue
    
    print(f"共找到 {len(total_list)} 集")
    return total_list

def download_short_drama(drama_info, episode_info):
    """下载短剧"""
    try:
        drama_name = drama_info[1]
        episode_num = episode_info[1]
        episode_title = episode_info[2]
        episode_id = episode_info[3]
        
        print(f"开始下载短剧: {drama_name} 第{episode_num}集 - {episode_title}")
        
        # 获取下载链接
        url = f"https://api.uuuka.com/v1/short_drama/episode/{episode_id}/download"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json'
        }
        
        req = urllib.request.Request(url, headers=headers)
        res = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
        data = json.load(res)
        
        if data.get('code') != 200 or not data.get('data') or not data['data'].get('url'):
            print("获取短剧下载链接失败")
            return False
            
        down_url = data['data']['url']
        
        # 下载文件
        download_dir = create_short_drama_dir()
        
        # 清理文件名中的非法字符
        filename = f'{drama_name}-第{episode_num}集-{episode_title}.mp4'
        invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # 缩短过长的文件名
        if len(filename) > 100:
            filename = filename[:50] + filename[-50:]
        
        filepath = os.path.join(download_dir, filename)
        
        # 使用通用下载函数
        success, final_filepath = download_file(down_url, f'{drama_name}-第{episode_num}集', episode_title, "mp4")
        
        if success:
            # 保存下载记录
            save_short_drama_history(drama_name, episode_num, "即刻短剧", final_filepath)
        return success
    except Exception as e:
        print(f"短剧下载失败: {type(e).__name__} - {str(e)}")
        return False

def play_short_drama(file_path):
    """播放短剧"""
    try:
        if not os.path.exists(file_path):
            print("文件不存在，无法播放")
            return False
        
        # 根据不同操作系统使用不同的播放命令
        if os.name == 'nt':  # Windows
            os.startfile(file_path)
        elif os.name == 'posix':  # macOS or Linux
            if sys.platform == 'darwin':  # macOS
                subprocess.call(('open', file_path))
            else:  # Linux
                subprocess.call(('xdg-open', file_path))
        
        print(f"正在播放: {os.path.basename(file_path)}")
        return True
    except Exception as e:
        print(f"播放失败: {type(e).__name__} - {str(e)}")
        return False

def handle_short_drama_command(command):
    """处理短剧命令"""
    parts = command.split()
    if len(parts) < 2:
        print_short_drama_help()
        return
    
    cmd = parts[1]
    
    if cmd == '-s' and len(parts) >= 3:
        # 搜索短剧
        keyword = ' '.join(parts[2:])
        dramas = search_short_drama(keyword)
        drama_list = display_short_drama_list(dramas, f"短剧搜索结果: {keyword}")
        
        if not drama_list:
            return
        
        # 选择短剧查看详情
        while True:
            try:
                choice = input("\n请输入您想要查看的短剧编号(输入0返回): ")
                if choice == "0":
                    break
                
                drama_idx = int(choice) - 1
                if 0 <= drama_idx < len(drama_list):
                    drama = drama_list[drama_idx]
                    drama_id = drama[4]
                    drama_name = drama[1]
                    
                    # 获取剧集列表
                    episodes = get_drama_episodes(drama_id)
                    episode_list = display_episode_list(episodes, drama_name)
                    
                    if not episode_list:
                        continue
                    
                    # 选择剧集下载或播放
                    while True:
                        try:
                            ep_choice = input("\n请输入您想要操作的剧集编号(输入0返回): ")
                            if ep_choice == "0":
                                break
                            
                            ep_idx = int(ep_choice) - 1
                            if 0 <= ep_idx < len(episode_list):
                                episode = episode_list[ep_idx]
                                
                                # 询问操作类型
                                action = input("请选择操作: 1.下载 2.播放 (输入1或2): ")
                                if action == "1":
                                    # 下载短剧
                                    download_short_drama(drama, episode)
                                elif action == "2":
                                    # 播放短剧 - 需要先下载
                                    print("播放功能需要先下载短剧")
                                    if download_short_drama(drama, episode):
                                        # 获取文件路径
                                        drama_name = drama[1]
                                        episode_num = episode[1]
                                        episode_title = episode[2]
                                        filename = f'{drama_name}-第{episode_num}集-{episode_title}.mp4'
                                        invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
                                        for char in invalid_chars:
                                            filename = filename.replace(char, '_')
                                        filepath = os.path.join(SHORT_DRAMA_DIR, filename)
                                        play_short_drama(filepath)
                                else:
                                    print("无效的操作选择")
                            else:
                                print("无效的剧集编号")
                        except ValueError:
                            print("请输入有效的数字")
                        except KeyboardInterrupt:
                            print("\n操作已取消")
                            break
                else:
                    print("无效的短剧编号")
            except ValueError:
                print("请输入有效的数字")
            except KeyboardInterrupt:
                print("\n操作已取消")
                break
    
    elif cmd == '-history':
        # 显示短剧下载历史
        show_short_drama_history()
    
    elif cmd == '-h':
        # 显示短剧帮助
        print_short_drama_help()
    
    else:
        print("无效的短剧命令")
        print_short_drama_help()

def print_short_drama_help():
    """显示短剧帮助信息"""
    print("\n===== 短剧命令帮助 =====")
    print("short -s [关键词]         搜索短剧")
    print("short -history           查看短剧下载历史")
    print("short -h                 显示短剧帮助")

# ============================= 主程序 =============================
def main():
    print("=== 音乐搜索与下载工具 ===")
    print("命令说明:")
    print("1. 输入歌曲名称 - 搜索歌曲")
    print("2. 输入 '/Singer:歌手名' - 搜索歌手的所有歌曲")
    print("3. 输入 'KuGou:音乐名' - 搜索酷狗音乐")
    print("4. 输入 '/SingerKuGou:歌手名' - 搜索酷狗歌手")
    print("5. 输入 'qq:音乐名' - 搜索QQ音乐")
    print("6. 输入 '/Singerqq:歌手名' - 搜索QQ歌手")
    print("7. 输入 'Cloud:音乐名' - 搜索网易云音乐")
    print("8. 输入 '/SingerCloud:歌手名' - 搜索网易云歌手")
    print("9. 输入 'All:音乐名' - 全网搜索（所有平台）")
    print("10. 输入 'history' - 查看下载历史")
    print("11. 输入 'short' - 进入短剧功能")
    print("12. 输入 'exit' - 退出程序")
    print(f"所有文件将下载到: {os.path.abspath(DOWNLOAD_DIR)}")
    print(f"短剧文件将下载到: {os.path.abspath(SHORT_DRAMA_DIR)}")
    
    # 初始化下载记录
    init_download_history()
    init_short_drama_history()
    
    while True:
        try:
            command = input('\n请输入命令: ').strip()
            
            if command.lower() == 'exit':
                print("感谢使用，再见！")
                break
            
            # 查看下载历史
            elif command.lower() == 'history':
                show_download_history()
                continue
            
            # 短剧功能
            elif command.startswith('short'):
                handle_short_drama_command(command)
                continue
            
            # 全网搜索命令
            elif command.startswith('All:'):
                keyword = command[4:].strip()
                if not keyword:
                    print("请输入搜索关键词")
                    continue
                
                results = search_all_platforms(keyword)
                song_list = display_all_platforms_results(results, f"全网搜索结果: {keyword}")
                process_download(song_list, download_from_all_platforms, "全网")
            
            # 酷狗音乐命令
            elif command.startswith('KuGou:'):
                keyword = command[6:].strip()
                if not keyword:
                    print("请输入搜索关键词")
                    continue
                
                print(f"正在酷狗搜索: {keyword}")
                songs = search_kugou(keyword)
                song_list = display_kugou_list(songs, f"酷狗搜索结果: {keyword}")
                process_download(song_list, download_kugou, "酷狗")
            
            # 酷狗歌手命令
            elif command.startswith('/SingerKuGou:'):
                artist_name = command[13:].strip()
                if not artist_name:
                    print("请输入歌手名称")
                    continue
                
                print(f"正在酷狗搜索歌手: {artist_name}")
                songs = search_kugou(artist_name)
                song_list = display_kugou_list(songs, f"酷狗歌手: {artist_name}")
                process_download(song_list, download_kugou, "酷狗")
            
            # QQ音乐命令
            elif command.startswith('qq:'):
                keyword = command[3:].strip()
                if not keyword:
                    print("请输入搜索关键词")
                    continue
                
                print(f"正在QQ音乐搜索: {keyword}")
                songs = search_qq(keyword)
                song_list = display_qq_list(songs, f"QQ音乐搜索结果: {keyword}")
                process_download(song_list, download_qq, "QQ音乐")
            
            # QQ歌手命令
            elif command.startswith('/Singerqq:'):
                artist_name = command[10:].strip()
                if not artist_name:
                    print("请输入歌手名称")
                    continue
                
                print(f"正在QQ音乐搜索歌手: {artist_name}")
                songs = search_qq(artist_name)
                song_list = display_qq_list(songs, f"QQ音乐歌手: {artist_name}")
                process_download(song_list, download_qq, "QQ音乐")
            
            # 网易云音乐命令
            elif command.startswith('Cloud:'):
                keyword = command[6:].strip()
                if not keyword:
                    print("请输入搜索关键词")
                    continue
                
                print(f"正在网易云音乐搜索: {keyword}")
                songs = search_cloud(keyword)
                song_list = display_cloud_list(songs, f"网易云音乐搜索结果: {keyword}")
                process_download(song_list, download_cloud, "网易云音乐")
            
            # 网易云歌手命令
            elif command.startswith('/SingerCloud:'):
                artist_name = command[13:].strip()
                if not artist_name:
                    print("请输入歌手名称")
                    continue
                
                print(f"正在网易云音乐搜索歌手: {artist_name}")
                songs = search_cloud(artist_name)
                song_list = display_cloud_list(songs, f"网易云音乐歌手: {artist_name}")
                process_download(song_list, download_cloud, "网易云音乐")
            
            # 歌手命令
            elif command.startswith('/Singer:'):
                artist_name = command[8:].strip()
                if not artist_name:
                    print("请输入歌手名称")
                    continue
                
                print(f"正在搜索歌手: {artist_name}")
                songs = search_songs(artist_name)
                song_list = display_song_list(songs, f"{artist_name} 的歌曲")
                process_download(song_list, download_song, "咪咕音乐")
            
            # 默认搜索
            else:
                print(f"正在搜索: {command}")
                songs = search_songs(command)
                song_list = display_song_list(songs, "搜索结果")
                process_download(song_list, download_song, "咪咕音乐")
                
        except UnicodeEncodeError:
            print("输入包含无法编码的字符，请重新输入")
        except KeyboardInterrupt:
            print("\n操作已取消")
        except Exception as e:
            print(f"发生未知错误: {type(e).__name__} - {str(e)}")

def process_download(item_list, download_func, platform_name):
    """处理下载选择"""
    if not item_list:
        print(f"{platform_name}没有找到可下载的内容")
        return
    
    while True:
        try:
            choice = input(f"\n请输入您想要下载的{platform_name}内容编号(多个编号用空格分隔，输入0返回): ")
            
            if choice == "0":
                break
                
            download_count = 0
            skip_count = 0
            for ch in choice.split():
                try:
                    ch_num = int(ch) - 1
                    if 0 <= ch_num < len(item_list):
                        item = item_list[ch_num]
                        if download_func(item):
                            download_count += 1
                        else:
                            skip_count += 1
                    else:
                        print(f"编号 {ch} 无效，跳过")
                        skip_count += 1
                except ValueError:
                    print(f"'{ch}' 不是有效的数字，跳过")
                    skip_count += 1
            
            print(f"\n成功下载 {download_count} 个项目, 跳过 {skip_count} 个项目")
            break
        except KeyboardInterrupt:
            print("\n下载已取消")
            break
        except Exception as e:
            print(f"处理下载时发生错误: {type(e).__name__} - {str(e)}")

if __name__ == "__main__":
    main()