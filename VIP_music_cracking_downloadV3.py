import urllib.request
import urllib.parse
import json
import time
import os
import socket
import re
import random
import string
import threading
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

REQUEST_TIMEOUT = 15
socket.setdefaulttimeout(REQUEST_TIMEOUT)

DOWNLOAD_DIR = "music_downloads"
DOWNLOAD_HISTORY_FILE = "Download_Log.csv"

def create_download_dir():
	""""""
	if not os.path.exists(DOWNLOAD_DIR):
		os.makedirs(DOWNLOAD_DIR)
		print(f"下载目录: {os.path.abspath(DOWNLOAD_DIR)}")
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
		print(f"记录已保存")
	except Exception as e:
		print(f"Failed: {str(e)}")

def show_download_history():
	""""""
	try:
		if not os.path.exists(DOWNLOAD_HISTORY_FILE):
			print("无")
			return
		
		with open(DOWNLOAD_HISTORY_FILE, 'r', encoding='utf-8') as f:
			reader = csv.reader(f)
			rows = list(reader)
			
			if len(rows) <= 1:
				print("无")
				return
			
			print("\n===== 下载历史 =====")
			for i, row in enumerate(rows[1:], 1):  # 跳过标题行
				print(f"{i}. {row[0]} - [{row[3]}] {row[1]} - {row[2]}")
			
			print(f"\n {len(rows)-1} ")
	except Exception as e:
		print(f"读取失败: {str(e)}")

def search_songs(keyword, page_size=500):
	""""""
	encoded_keyword = urllib.parse.quote(keyword)
	url = f'https://c.musicapp.migu.cn/v1.0/content/search_all.do?text={encoded_keyword}&pageNo=1&pageSize={page_size}&isCopyright=1&sort=1&searchSwitch=%7B%22song%22%3A1%2C%22album%22%3A0%2C%22singer%22%3A0%2C%22tagSong%22%3A1%2C%22mvSong%22%3A0%2C%22bestShow%22%3A1%7D'
	
	try:
		req = urllib.request.Request(url, headers={'channel': '0140210'})
		res = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
		data = json.load(res)
		
		if 'songResultData' in data and 'result' in data['songResultData']:
			return data['songResultData']['result']
		print("APIError")
		return []
	except urllib.error.URLError as e:
		print(f"Network Error: {e.reason}")
	except urllib.error.HTTPError as e:
		print(f"HTTPError: {e.code} - {e.reason}")
	except socket.timeout:
		print("Timeout")
	except json.JSONDecodeError:
		print("APIParse Error")
	except Exception as e:
		print(f"Search Error: {type(e).__name__} - {str(e)}")
	return []

def display_song_list(song_list, title="Search successful"):
	""""""
	if not song_list:
		print("Not found")
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
			print(f"Handling error: {type(e).__name__} - {str(e)}")
			continue
	
	print(f"Find {len(total_list)} song")
	return total_list

def download_song(song):
	""""""
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
				print("Download failed")
				return False
				
			down_url = data['data']['url']
		except Exception as e:
			print(f"Download Error: {type(e).__name__} - {str(e)}")
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
							
							downloaded_mb = downloaded / (1024 * 1024)
							total_mb = total_size / (1024 * 1024)
							
							print(f"\rMusic downloading........ {downloaded_mb:.1f}/{total_mb:.1f} MB {speed:.1f} kB/s eta {eta_str}", end='')
						else:
							print(f"\r已下载: {downloaded} kib", end='')
					except socket.timeout:
						print("\nDownload Error")
						continue
			
			print('\nSuccess!')
			print(f"File: {os.path.abspath(filepath)}")
			
			save_download_history(song_name, singers, "咪咕音乐", filepath)
			return True
		except Exception as e:
			print(f"下载失败: {type(e).__name__} - {str(e)}")
			return False
	except Exception as e:
		print(f"下载过程中发生错误: {type(e).__name__} - {str(e)}")
		return False

def search_kugou(keyword):
	"""搜索酷狗音乐 - 使用稳定可靠的API"""
	try:
		encoded_keyword = urllib.parse.quote(keyword)
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
	""""""
	try:
		song_name = song[1]
		singers = song[2]
		file_hash = song[3]
		album_id = song[4]
		
		print(f"开始下载酷狗音乐: {song_name} - {singers}")
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
		if not down_url.startswith('http'):
			print("酷狗下载链接无效")
			return False
			
		success, filepath = download_file(down_url, song_name, singers, "mp3")
		if success:
			save_download_history(song_name, singers, "酷狗音乐", filepath)
		return success
	except Exception as e:
		print(f"酷狗下载失败: {type(e).__name__} - {str(e)}")
		return False

def search_qq(keyword):
	""""""
	try:
		encoded_keyword = urllib.parse.quote(keyword)
		url = f"https://c.y.qq.com/soso/fcgi-bin/client_search_cp?p=1&n=20&w={encoded_keyword}&format=json"
		
		headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
			'Referer': 'https://y.qq.com/'
		}
		
		req = urllib.request.Request(url, headers=headers)
		res = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
		raw_data = res.read().decode('utf-8')
		
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
	"""I"""
	try:
		song_name = song[1]
		singers = song[2]
		song_mid = song[3]
		
		print(f"开始下载QQ音乐: {song_name} - {singers}")
		
		url = f"https://u.y.qq.com/cgi-bin/musicu.fcg?format=json&data=%7B%22req_0%22%3A%7B%22module%22%3A%22vkey.GetVkeyServer%22%2C%22method%22%3A%22CgiGetVkey%22%2C%22param%22%3A%7B%22guid%22%3A%22358840384%22%2C%22songmid%22%3A%5B%22{song_mid}%22%5D%2C%22songtype%22%3A%5B0%5D%2C%22uin%22%3A%221443481947%22%2C%22loginflag%22%3A1%2C%22platform%22%3A%2220%22%7D%7D%2C%22comm%22%3A%7B%22uin%22%3A%2218585073516%22%2C%22format%22%3A%22json%22%2C%22ct%22%3A24%2C%22cv%22%3A0%7D%7D"
		
		headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
			'Referer': 'https://y.qq.com/'
		}
		
		req = urllib.request.Request(url, headers=headers)
		res = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
		data = json.load(res)
		
		try:
			purl = data['req_0']['data']['midurlinfo'][0]['purl']
			if not purl:
				print("获取QQ音乐下载链接失败")
				return False
			
			down_url = f"https://dl.stream.qqmusic.qq.com/{purl}"
			success, filepath = download_file(down_url, song_name, singers, "m4a")
			if success:
				save_download_history(song_name, singers, "QQ音乐", filepath)
			return success
		except (KeyError, IndexError):
			print("解析QQ音乐下载链接失败")
			return False
	except Exception as e:
		print(f"QQ音乐下载失败: {type(e).__name__} - {str(e)}")
		return False

def search_cloud(keyword):
	""""""
	try:
		encoded_keyword = urllib.parse.quote(keyword)
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
			song_name = song.get('name', '未知歌曲')
			singers = '、'.join([s['name'] for s in song.get('ar', [])]) or '未知歌手'
			song_id = song.get('id', '')
			
			if not song_id:
				continue
				
			total_list.append([idx, song_name, singers, song_id])
			print(f"{idx}. {song_name} - {singers}")
		except Exception as e:
			print(f"处理网易云音乐歌曲数据时出错: {str(e)}")
			continue
	
	print(f"共找到 {len(total_list)} 首歌曲")
	return total_list

def download_cloud(song):
	"""下载网易云音乐 - 使用稳定可靠的API"""
	try:
		song_name = song[1]
		singers = song[2]
		song_id = song[3]
		
		print(f"开始下载网易云音乐: {song_name} - {singers}")
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
		success, filepath = download_file(down_url, song_name, singers, "mp3")
		if success:
			save_download_history(song_name, singers, "网易云音乐", filepath)
		return success
	except Exception as e:
		print(f"网易云音乐下载失败: {type(e).__name__} - {str(e)}")
		return False

def download_file(url, title, creator, ext):
	"""通用文件下载函数 - 增强稳定性和错误处理"""
	try:
		url = urllib.parse.unquote(url)
		
		headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
			'Referer': 'https://www.google.com/',
			'Accept': '*/*',
			'Connection': 'keep-alive'
		}
		
		req = urllib.request.Request(url, headers=headers)
		with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as res:
			if res.status != 200:
				print(f"下载失败: HTTP状态码 {res.status}")
				return False, None
				
			content_type = res.headers.get('Content-Type', '')
			if 'html' in content_type or 'text' in content_type:
				print("下载链接无效，返回了HTML内容")
				return False, None
				
			content_length = res.headers.get('Content-Length')
			total_size = int(content_length) if content_length else 0
			downloaded = 0
			chunk_size = 1024 * 8
			
			download_dir = create_download_dir()
			
			filename = f'{title}-{creator}.{ext}'
			invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
			for char in invalid_chars:
				filename = filename.replace(char, '_')
			
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
	
							elapsed_time = time.time() - start_time
							if elapsed_time > 0:
								speed = downloaded / elapsed_time / 1024  
								remaining = (total_size - downloaded) / (speed * 1024) if speed > 0 else 0
								eta_min = int(remaining // 60)
								eta_sec = int(remaining % 60)
								eta_str = f"{eta_min}:{eta_sec:02d}"
							else:
								speed = 0
								eta_str = "0:00"
							
							downloaded_mb = downloaded / (1024 * 1024)
							total_mb = total_size / (1024 * 1024)
							
							print(f"\rMusic downloading........ {downloaded_mb:.1f}/{total_mb:.1f} MB {speed:.1f} kB/s eta {eta_str}", end='')
						else:
							print(f"\r已下载: {downloaded} B", end='')
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

def search_all_platforms(keyword, max_results=10):
	"""全网搜索 - 同时搜索所有平台"""
	print(f"正在全网搜索: {keyword}")

	all_results = []
	
	search_functions = [
		("咪咕音乐", search_songs),
		("酷狗音乐", search_kugou),
		("QQ音乐", search_qq),
		("网易云音乐", search_cloud)
	]
	
	with ThreadPoolExecutor(max_workers=4) as executor:
		future_to_platform = {
			executor.submit(search_func, keyword): (platform_name, search_func) 
			for platform_name, search_func in search_functions
		}
		
		for future in as_completed(future_to_platform):
			platform_name, search_func = future_to_platform[future]
			try:
				results = future.result()
				if results:
					print(f"{platform_name}找到 {len(results)} 个结果")
					for result in results[:max_results]:
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
			
			if platform == "咪咕音乐":
				song_name = data.get('name', '未知歌曲')
				singers = data.get('singers', [{}])[0].get('name', '未知歌手')
				contentId = data.get('contentId', '')
				copyrightId = data.get('copyrightId', '')
				album_info = data.get('albums', [{}])[0] if data.get('albums') else {}
				albumId = album_info.get('id', '0')
				
				if not contentId or not copyrightId:
					continue
					
				total_list.append([idx, song_name, singers, contentId, copyrightId, albumId, platform])
				print(f"{idx}. [{platform}] {song_name} - {singers}")
				
			elif platform == "酷狗音乐":
				song_name = data.get('SongName', '未知歌曲')
				singers = data.get('SingerName', '未知歌手')
				file_hash = data.get('FileHash', '')
				album_id = data.get('AlbumID', '')
				
				if not file_hash:
					continue
					
				total_list.append([idx, song_name, singers, file_hash, album_id, '', platform])
				print(f"{idx}. [{platform}] {song_name} - {singers}")
				
			elif platform == "QQ音乐":
				song_name = data.get('songname', '未知歌曲')
				singers = '、'.join([s['name'] for s in data.get('singer', [])]) or '未知歌手'
				song_mid = data.get('songmid', '')
				
				if not song_mid:
					continue
					
				total_list.append([idx, song_name, singers, song_mid, '', '', platform])
				print(f"{idx}. [{platform}] {song_name} - {singers}")
				
			elif platform == "网易云音乐":
				song_name = data.get('name', '未知歌曲')
				singers = '、'.join([s['name'] for s in data.get('ar', [])]) or '未知歌手'
				song_id = data.get('id', '')
				
				if not song_id:
					continue
					
				total_list.append([idx, song_name, singers, song_id, '', '', platform])
				print(f"{idx}. [{platform}] {song_name} - {singers}")
				
		except Exception as e:
			print(f"处理全网搜索结果时出错: {str(e)}")
			continue
	
	print(f"全网共找到 {len(total_list)} 首歌曲")
	return total_list

def download_from_all_platforms(song):
	"""从全网搜索结果中下载歌曲"""
	try:
		platform = song[6] 
		
		if platform == "咪咕音乐":
			contentId = song[3]
			copyrightId = song[4]
			albumId = song[5]
			song_name = song[1]
			singers = song[2]
			
			print(f"开始下载咪咕音乐: {song_name} - {singers}")
			
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
			success, filepath = download_file(down_url, song_name, singers, "mp3")
			if success:
				save_download_history(song_name, singers, "咪咕音乐", filepath)
			return success
			
		elif platform == "酷狗音乐":
			return download_kugou(song)
			
		elif platform == "QQ音乐":
			return download_qq(song)
			
		elif platform == "网易云音乐":
			return download_cloud(song)
			
	except Exception as e:
		print(f"全网下载失败: {type(e).__name__} - {str(e)}")
		return False

def main():
	print('''     ██████╗ ██████╗  █████╗  ██████╗
     ██╔══██╗██╔══██╗██╔══██╗██╔════╝
     ██████╔╝██████╔╝███████║██║     
     ██╔══██╗██╔══██╗██╔══██║██║     
     ██║  ██║██████╔╝██║  ██║╚██████╗
     ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝ ╚═════╝
''')
	print("Command description:")
	print("1. Enter a song name-search for a song")
	print("2. Input '/ Singer: artist name' - searches for all songs by the artist")
	print("3. Enter 'KuGou: music name' - search for Kugou music")
	print("4. Input '/ SingerKuGou: artist name' - search for cool dog songs")
	print("5. Enter 'qq: music name' - search for qq music")
	print("6. Input '/ Singerqq: artist name' - search qq artist")
	print("7. Enter 'Cloud: music name' - Search Netease Cloud Music")
	print("8. Input '/ SingerCloud: singer Name' - Search Netease Cloud Singer")
	print("9. Enter 'All: music Name' - Search all over the web (all platforms)")
	print("10. The command of history is' history'")
	print("11.Input' exit' - quit a program")
	print(f"File download to: {os.path.abspath(DOWNLOAD_DIR)}")
	
	init_download_history()
	
	while True:
		try:
			command = input('\n/> ').strip()
			
			if command.lower() == 'exit':
				print("exit")
				break
		
			elif command.lower() == 'history':
				show_download_history()
				continue
			
			elif command.startswith('All:'):
				keyword = command[4:].strip()
				if not keyword:
					print("请输入搜索关键词")
					continue
				
				results = search_all_platforms(keyword)
				song_list = display_all_platforms_results(results, f"全网搜索结果: {keyword}")
				process_download(song_list, download_from_all_platforms, "全网")
			
	
			elif command.startswith('KuGou:'):
				keyword = command[6:].strip()
				if not keyword:
					print("请输入搜索关键词")
					continue
				
				print(f"正在酷狗搜索: {keyword}")
				songs = search_kugou(keyword)
				song_list = display_kugou_list(songs, f"酷狗搜索结果: {keyword}")
				process_download(song_list, download_kugou, "酷狗")
			
		
			elif command.startswith('/SingerKuGou:'):
				artist_name = command[13:].strip()
				if not artist_name:
					print("请输入歌手名称")
					continue
				
				print(f"正在酷狗搜索歌手: {artist_name}")
				songs = search_kugou(artist_name)
				song_list = display_kugou_list(songs, f"酷狗歌手: {artist_name}")
				process_download(song_list, download_kugou, "酷狗")
			
			elif command.startswith('qq:'):
				keyword = command[3:].strip()
				if not keyword:
					print("请输入搜索关键词")
					continue
				
				print(f"正在QQ音乐搜索: {keyword}")
				songs = search_qq(keyword)
				song_list = display_qq_list(songs, f"QQ音乐搜索结果: {keyword}")
				process_download(song_list, download_qq, "QQ音乐")
			
			elif command.startswith('/Singerqq:'):
				artist_name = command[10:].strip()
				if not artist_name:
					print("请输入歌手名称")
					continue
				
				print(f"正在QQ音乐搜索歌手: {artist_name}")
				songs = search_qq(artist_name)
				song_list = display_qq_list(songs, f"QQ音乐歌手: {artist_name}")
				process_download(song_list, download_qq, "QQ音乐")
		
			elif command.startswith('Cloud:'):
				keyword = command[6:].strip()
				if not keyword:
					print("请输入搜索关键词")
					continue
				
				print(f"正在网易云音乐搜索: {keyword}")
				songs = search_cloud(keyword)
				song_list = display_cloud_list(songs, f"网易云音乐搜索结果: {keyword}")
				process_download(song_list, download_cloud, "网易云音乐")
			
			elif command.startswith('/SingerCloud:'):
				artist_name = command[13:].strip()
				if not artist_name:
					print("请输入歌手名称")
					continue
				
				print(f"正在网易云音乐搜索歌手: {artist_name}")
				songs = search_cloud(artist_name)
				song_list = display_cloud_list(songs, f"网易云音乐歌手: {artist_name}")
				process_download(song_list, download_cloud, "网易云音乐")
			
			elif command.startswith('/Singer:'):
				artist_name = command[8:].strip()
				if not artist_name:
					print("请输入歌手名称")
					continue
				
				print(f"正在搜索歌手: {artist_name}")
				songs = search_songs(artist_name)
				song_list = display_song_list(songs, f"{artist_name} 的歌曲")
				process_download(song_list, download_song, "咪咕音乐")
			
			else:
				print(f"正在搜索: {command}")
				songs = search_songs(command)
				song_list = display_song_list(songs, "搜索结果")
				process_download(song_list, download_song, "咪咕音乐")
				
		except UnicodeEncodeError:
			print("No")
		except KeyboardInterrupt:
			print("\n操作已取消")
		except Exception as e:
			print(f"Error: {type(e).__name__} - {str(e)}")

def process_download(item_list, download_func, platform_name):
	"""处理下载选择"""
	if not item_list:
		print(f"{platform_name}Not found")
		return
	
	while True:
		try:
			choice = input(f"\ndownload{platform_name}（0~20）>")
			
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