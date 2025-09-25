#音乐下载工具(_T)
音乐下载工具(_T)
 
一个轻量实用的python音乐下载工具，专注VIP音乐解析与免费保存 🎵
-全终端适配：完美支持Linux、macOS、Windows及安卓Termux终端环境，是命令行听歌利器
-双版本适配：提供VIP_music_cracking_download.py和VIP_music_cracking_download2.py两个版本，满足不同场景需求
-开源共享：基于GPLv2协议开源，欢迎开发者学习、改进并反馈
 
快速上手
 
环境要求
 
-Python3.6及以上版本
-(可选)终端音频播放器(如mpg123、ffplay、cmus等，用于下载后直接播放）
 
终端音频播放器安装（分平台详解）
 
🔹 Linux 系统
 
-安装mpg123(轻量MP3播放器)：
bash
  

#Ubuntu/Debian
sudo apt-get install mpg123
#Centos/RHEL
sudo yum install mpg123
 
-安装cmus(功能强大的终端音乐播放器)：
bash
  

#Ubuntu/Debian
sudo apt-get install cmus
#Centos/RHEL
sudo yum install cmus
 
 
🔹 macOS 系统
 
通过 Homebrew 安装：
 
bash
  

brew安装mpg123
#或
brew安装cmus
 
 
🔹  Windows系统
 
安装ffmpeg套件（含ffplay播放器）：
 
1.从ffmpeg官网下载Windows版本
2.将bin目录加入系统环境变量
3.播放命令：ffplay音乐文件.MP3
 
🔹 安卓Termux环境
 
1.安装Termux：
-打开安卓手机的F-Droid应用商店或Termux官网，下载并安装Termux应用。
2.在Termux中安装依赖：
猛击
  

#安装python（若未安装）
包装安装python-y
#安装mpg123播放器
包装安装mpg123-y
 
 
使用步骤
 
1. 克隆仓库到本地
猛击
  

git克隆https://github.com/httpspycharmhelpers/Music-download_tool.git
 
2. 进入项目目录
猛击
  

CD音乐下载工具
 
3. 运行工具并下载音乐
猛击
  

#选择版本1
Python VIP_music_cracking_download.py
# 或选择版本2
python VIP_music_cracking_download2.py
 
4. 下载完成后，用终端播放器直接播放（以  mpg123  为例）
bash
  

mpg123 下载的音乐文件.mp3
 
 
注意事项
 
- 仅限个人学习研究：本工具严禁用于商业用途，请勿侵犯音乐版权
- 支持正版音乐：请尊重创作者劳动成果，条件允许时优先选择正版
- 开源协议约束：基于 GPLv2 协议，任何衍生作品也必须开源并遵循相同协议
 
许可证
 
本项目采用 GNU通用公共许可证第2版（GPLv2） 开源，详见 LICENSE 文件。
