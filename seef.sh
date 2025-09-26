#!/bin/bash

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查Python环境
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 --version 2>&1)
        log_success "找到 Python3: $PYTHON_VERSION"
        return 0
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        PYTHON_VERSION=$(python --version 2>&1)
        log_success "找到 Python: $PYTHON_VERSION"
        return 0
    else
        log_error "未找到Python环境！"
        return 1
    fi
}

# 安装Python (Linux/macOS)
install_python_linux() {
    log_info "正在尝试安装Python3..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # 检测Linux发行版
        if command -v apt-get &> /dev/null; then
            log_info "检测到Debian/Ubuntu系统，使用apt安装..."
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip
        elif command -v yum &> /dev/null; then
            log_info "检测到CentOS/RHEL系统，使用yum安装..."
            sudo yum install -y python3 python3-pip
        elif command -v pacman &> /dev/null; then
            log_info "检测到Arch Linux系统，使用pacman安装..."
            sudo pacman -S python python-pip
        else
            log_error "无法自动识别包管理器，请手动安装Python3"
            log_info "请访问: https://www.python.org/downloads/"
            return 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        log_info "检测到macOS系统..."
        if command -v brew &> /dev/null; then
            brew install python3
        else
            log_error "请先安装Homebrew或手动安装Python3"
            log_info "下载地址: https://www.python.org/downloads/macos/"
            return 1
        fi
    else
        log_error "不支持的系统类型: $OSTYPE"
        return 1
    fi
    
    if check_python; then
        log_success "Python安装成功！"
        return 0
    else
        log_error "Python安装失败！"
        return 1
    fi
}

# 安装依赖
install_requirements() {
    log_info "检查Python依赖..."
    if [ -f "requirements.txt" ]; then
        log_info "正在安装依赖包..."
        $PYTHON_CMD -m pip install -r requirements.txt
        if [ $? -eq 0 ]; then
            log_success "依赖安装完成！"
        else
            log_warning "部分依赖安装失败，尝试继续运行..."
        fi
    else
        log_info "未找到requirements.txt，跳过依赖安装"
    fi
}

# 启动主程序
start_main() {
    log_info "启动主程序 - VIP音乐下载工具..."
    if [ -f "VIP_music_cracking_download.py" ]; then
        $PYTHON_CMD VIP_music_cracking_download.py
    else
        log_error "未找到主程序文件: VIP_music_cracking_download.py"
        return 1
    fi
}

# 启动备用程序
start_alternative() {
    log_info "启动备用程序 - VIP音乐下载工具V2..."
    if [ -f "VIP_music_cracking_downloadV2.py" ]; then
        $PYTHON_CMD VIP_music_cracking_downloadV2.py
    else
        log_error "未找到备用程序文件: VIP_music_cracking_downloadV2.py"
        return 1
    fi
}

# 显示帮助信息
show_help() {
    echo "音乐下载工具 - 使用说明"
    echo "================================"
    echo "用法: seef [选项]"
    echo ""
    echo "选项:"
    echo "  (无参数)   启动主程序"
    echo "  -a        启动备用程序(V2版本)"
    echo "  -p        检查/安装Python环境"
    echo "  -pa/-ap   自动安装Python并启动备用程序"
    echo "  -h        显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  seef         # 启动主下载工具"
    echo "  seef -a      # 启动V2版本"
    echo "  seef -pa     # 全自动安装并启动(推荐新手)"
    echo ""
    echo "项目地址: https://github.com/httpspycharmhelpers/Music-download_tool"
}

# 主函数
main() {
    case "$1" in
        "-a"|"--alternative")
            if check_python; then
                install_requirements
                start_alternative
            else
                log_error "Python未安装，请使用 'seef -pa' 自动安装"
            fi
            ;;
        "-p"|"--python")
            if ! check_python; then
                install_python_linux
            fi
            ;;
        "-pa"|"-ap"|"--auto")
            if ! check_python; then
                log_info "开始自动安装Python环境..."
                install_python_linux
            fi
            if check_python; then
                install_requirements
                start_alternative
            else
                log_error "Python环境安装失败，请手动安装"
            fi
            ;;
        "-h"|"--help")
            show_help
            ;;
        "")
            if check_python; then
                install_requirements
                start_main
            else
                log_error "Python未安装，请使用 'seef -pa' 自动安装"
            fi
            ;;
        *)
            log_error "未知参数: $1"
            show_help
            ;;
    esac
}

# 显示欢迎信息
echo "========================================"
echo "  音乐下载工具 - VIP音乐解析下载"
echo "  https://github.com/httpspycharmhelpers"
echo "========================================"

# 执行主函数
main "$1"
