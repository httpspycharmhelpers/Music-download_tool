# Music-download_tool
Music-download_tool
 
一个轻量实用的 Python 音乐下载工具，专注 VIP 音乐解析与免费保存 🎵
 
功能亮点
 
- VIP 音乐自由：一键解析并保存平台 VIP 音乐，打破“付费壁垒”
- 全终端适配：完美支持 Linux、macOS、Windows 及安卓 Termux 终端环境，是热爱命令行“终端宝贝”的听歌利器
- 双版本适配：提供  VIP_music_cracking_download.py  和  VIP_music_cracking_download2.py  两个版本，满足不同场景需求
- 开源共享：基于 GPLv2 协议开源，欢迎开发者学习、改进并反馈
 
快速上手
 
环境要求
 
- Python 3.6 及以上版本
- （可选）终端音频播放器（如  mpg123 、 ffplay 、 cmus  等，用于下载后直接播放）
 
终端音频播放器安装（分平台详解）
 
🔹 Linux 系统
 
- 安装  mpg123 （轻量 MP3 播放器）：
bash
  

# Ubuntu/Debian
sudo apt-get install mpg123
# CentOS/RHEL
sudo yum install mpg123
 
- 安装  cmus （功能强大的终端音乐播放器）：
bash
  

# Ubuntu/Debian
sudo apt-get install cmus
# CentOS/RHEL
sudo yum install cmus
 
 
🔹 macOS 系统
 
通过 Homebrew 安装：
 
bash
  

brew install mpg123
# 或
brew install cmus
 
 
🔹 Windows 系统
 
安装  ffmpeg  套件（含  ffplay  播放器）：
 
1. 从 ffmpeg 官网 下载 Windows 版本
2. 将  bin  目录加入系统环境变量
3. 播放命令： ffplay 音乐文件.mp3 
 
🔹 安卓 Termux 环境
 
1. 安装 Termux：
- 打开安卓手机的 F-Droid 应用商店 或 Termux 官网，下载并安装 Termux 应用。
2. 在 Termux 中安装依赖：
bash
  

# 安装 Python（若未安装）
pkg install python -y
# 安装 mpg123 播放器
pkg install mpg123 -y
 
 
使用步骤
 
1. 克隆仓库到本地
bash
  

git clone https://github.com/httpspycharmhelpers/Music-download_tool.git
 
2. 进入项目目录
bash
  

cd Music-download_tool
 
3. 运行工具并下载音乐
bash
  

# 选择版本1
python VIP_music_cracking_download.py
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
