@echo off
chcp 65001 >nul
title Music Download Tool

echo ========================================
echo   音乐下载工具 - VIP音乐解析下载
echo   https://github.com/httpspycharmhelpers
echo ========================================

:: 设置颜色
for /f "delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do set "DEL=%%a"
set "RED=%DEL%[91m"
set "GREEN=%DEL%[92m"
set "YELLOW=%DEL%[93m"
set "BLUE=%DEL%[94m"
set "RESET=%DEL%[0m"

:: 日志函数
:log_info
echo %BLUE%[INFO]%RESET% %*
exit /b

:log_success
echo %GREEN%[SUCCESS]%RESET% %*
exit /b

:log_warning
echo %YELLOW%[WARNING]%RESET% %*
exit /b

:log_error
echo %RED%[ERROR]%RESET% %*
exit /b

:: 检查Python环境
:check_python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    call :log_success "找到 Python:"
    python --version
    set PYTHON_CMD=python
    exit /b 0
)

python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    call :log_success "找到 Python3:"
    python3 --version
    set PYTHON_CMD=python3
    exit /b 0
)

call :log_error "未找到Python环境！"
exit /b 1

:: 安装Python (Windows)
:install_python
call :log_info "正在引导安装Python..."
call :log_info "下载地址: https://www.python.org/downloads/"
call :log_info "请下载Python 3.6或更高版本"
call :log_info "安装时务必勾选 'Add Python to PATH' 选项"
pause
start https://www.python.org/downloads/
exit /b 1

:: 安装依赖
:install_requirements
if exist requirements.txt (
    call :log_info "正在安装Python依赖..."
    %PYTHON_CMD% -m pip install -r requirements.txt
    if %errorlevel% equ 0 (
        call :log_success "依赖安装完成！"
    ) else (
        call :log_warning "依赖安装失败，尝试继续运行..."
    )
) else (
    call :log_info "未找到requirements.txt，跳过依赖安装"
)
exit /b 0

:: 启动主程序
:start_main
call :log_info "启动主程序 - VIP音乐下载工具..."
if exist "VIP_music_cracking_download.py" (
    %PYTHON_CMD% VIP_music_cracking_download.py
) else (
    call :log_error "未找到主程序文件: VIP_music_cracking_download.py"
)
exit /b 0

:: 启动备用程序
:start_alternative
call :log_info "启动备用程序 - VIP音乐下载工具V2..."
if exist "VIP_music_cracking_downloadV2.py" (
    %PYTHON_CMD% VIP_music_cracking_downloadV2.py
) else (
    call :log_error "未找到备用程序文件: VIP_music_cracking_downloadV2.py"
)
exit /b 0

:: 显示帮助
:show_help
echo.
echo 音乐下载工具 - 使用说明
echo ================================
echo 用法: seef [选项]
echo.
echo 选项:
echo   (无参数)   启动主程序
echo   -a        启动备用程序(V2版本)
echo   -p        检查Python环境
echo   -pa       引导安装Python并启动备用程序
echo   -h        显示此帮助信息
echo.
echo 示例:
echo   seef         # 启动主下载工具
echo   seef -a      # 启动V2版本
echo   seef -pa     # 引导安装Python并启动
echo.
goto :eof

:: 主逻辑
setlocal enabledelayedexpansion

if "%1"=="-a" (
    call :check_python
    if !errorlevel! equ 0 (
        call :install_requirements
        call :start_alternative
    ) else (
        call :log_error "Python未安装，请使用 'seef -pa' 引导安装"
    )
) else if "%1"=="-p" (
    call :check_python
) else if "%1"=="-pa" (
    call :check_python
    if !errorlevel! equ 1 (
        call :install_python
        if !errorlevel! equ 0 (
            call :install_requirements
            call :start_alternative
        )
    ) else (
        call :install_requirements
        call :start_alternative
    )
) else if "%1"=="-h" (
    call :show_help
) else if "%1"=="" (
    call :check_python
    if !errorlevel! equ 0 (
        call :install_requirements
        call :start_main
    ) else (
        call :log_error "Python未安装，请使用 'seef -pa' 引导安装"
    )
) else (
    call :log_error "未知参数: %1"
    call :show_help
)

endlocal
pause
