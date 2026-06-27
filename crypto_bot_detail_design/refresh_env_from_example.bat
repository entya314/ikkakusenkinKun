@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

if not exist ".env.example" (
    echo .env.example が見つかりません。
    pause
    exit /b 1
)

set "ACCESS_KEY="
set "SECRET_KEY="

if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        if "%%A"=="COINCHECK_ACCESS_KEY" set "ACCESS_KEY=%%B"
        if "%%A"=="COINCHECK_SECRET_KEY" set "SECRET_KEY=%%B"
    )
    copy /Y ".env" ".env.backup" >nul
    echo 既存の .env を .env.backup にバックアップしました。
)

(
    for /f "usebackq delims=" %%L in (".env.example") do (
        set "LINE=%%L"
        if "!LINE:~0,20!"=="COINCHECK_ACCESS_KEY" (
            echo COINCHECK_ACCESS_KEY=!ACCESS_KEY!
        ) else if "!LINE:~0,20!"=="COINCHECK_SECRET_KEY" (
            echo COINCHECK_SECRET_KEY=!SECRET_KEY!
        ) else (
            echo !LINE!
        )
    )
) > ".env.tmp"

move /Y ".env.tmp" ".env" >nul

echo .env.example から .env を更新しました。
if defined ACCESS_KEY (
    echo COINCHECK_ACCESS_KEY は既存値を引き継ぎました。
) else (
    echo COINCHECK_ACCESS_KEY は未設定です。.env を開いて入力してください。
)
if defined SECRET_KEY (
    echo COINCHECK_SECRET_KEY は既存値を引き継ぎました。
) else (
    echo COINCHECK_SECRET_KEY は未設定です。.env を開いて入力してください。
)

pause
