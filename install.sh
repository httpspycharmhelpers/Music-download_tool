#!/bin/bash

echo "========================================"
echo "  音乐下载工具 - 自动安装脚本"
echo "========================================"

# 获取当前目录
CURRENT_DIR=$(pwd)

# 给seef.sh添加执行权限
chmod +x seef.sh

echo "检测系统环境..."
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    # Linux/macOS系统
    echo "检测到Linux/macOS系统"
    
    # 尝试创建全局符号链接
    if command -v sudo &> /dev/null; then
        echo "正在创建全局命令 'seef'..."
        sudo ln -sf "$CURRENT_DIR/seef.sh" /usr/local/bin/seef 2>/dev/null && {
            echo "✓ 全局命令 'seef' 创建成功！"
            echo "现在可以在任何目录使用 'seef' 命令了"
        } || {
            echo "⚠ 无法创建全局链接，使用本地脚本"
            echo "提示: 可以手动添加别名到 ~/.bashrc 或 ~/.zshrc:"
            echo "alias seef='$CURRENT_DIR/seef.sh'"
        }
    else
        ln -sf "$CURRENT_DIR/seef.sh" /usr/local/bin/seef 2>/dev/null && {
            echo "✓ 全局命令 'seef' 创建成功！"
        } || {
            echo "⚠ 无法创建全局链接"
        }
    fi
    
    echo ""
    echo "安装完成！使用方法："
    echo "  seef       - 启动主程序"
    echo "  seef -a    - 启动V2版本"
    echo "  seef -pa   - 自动安装Python并启动(推荐新手)"
    
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows系统
    echo "检测到Windows系统"
    echo ""
    echo "Windows安装说明："
    echo "1. 建议将当前目录添加到PATH环境变量"
    echo "2. 或者直接运行: seef.bat"
    echo ""
    echo "使用方法："
    echo "  seef.bat       - 启动主程序"
    echo "  seef.bat -a    - 启动V2版本"
    echo "  seef.bat -pa   - 引导安装Python并启动"
    
else
    echo "未知系统类型: $OSTYPE"
    echo "请手动运行脚本:"
    echo "  ./seef.sh    (Linux/macOS)"
    echo "  seef.bat     (Windows)"
fi

echo ""
echo "========================================"
echo "  快速开始："
echo "  seef -pa     # 一键自动安装并启动"
echo "========================================"
