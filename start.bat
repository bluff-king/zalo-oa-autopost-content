@echo off
rem Thay đổi thư mục làm việc thành thư mục chứa file .bat này
cd /d "%~dp0"

echo [INFO] Starting services...

rem Bắt đầu mỗi script trong một cửa sổ riêng và giám sát nó
start "API Server" cmd /c "call :LoopScript Add_Link_Input_Post_OA.py"
start "Scheduler" cmd /c "call :LoopScript Scheduler.py"

rem Kết thúc script chính, để lại 2 cửa sổ kia chạy
goto :eof

rem --- Subroutine để chạy và giám sát một script ---
:LoopScript
    set "SCRIPT_NAME=%~1"
    :LOOP
        echo [INFO] Starting script: %SCRIPT_NAME%
        
        rem Kích hoạt môi trường ảo nếu tồn tại
        if exist "venv\Scripts\activate.bat" (
            echo [INFO] Activating virtual environment...
            call "venv\Scripts\activate.bat"
        )
        
        rem Chạy script Python
        python "%SCRIPT_NAME%"
        
        echo [WARNING] Script '%SCRIPT_NAME%' has stopped. Restarting in 5 seconds...
        timeout /t 5 /nobreak
    goto LOOP
goto :eof
