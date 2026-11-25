@echo off
chcp 65001 > nul
set PATH=C:\Users\user\AppData\Local\Programs\Git\cmd;%PATH%
cd /d "%~dp0"

echo ========================================================
echo   [맛잇khu만] GitHub 푸시 및 Render 자동 재배포
echo ========================================================
echo.
echo 1. GitHub 기기 인증을 시작합니다.
echo    화면에 8자리 코드(예: ABCD-1234)가 뜨면
echo    웹 브라우저의 https://github.com/login/device 에 입력해주세요.
echo.
start https://github.com/login/device
git-credential-manager github login --device

echo.
echo 2. GitHub로 최신 코드를 푸시합니다...
git push origin main

echo.
echo ========================================================
echo   [성공] 푸시가 완료되었습니다!
echo   Render 대시보드에서 1~2분 내로 자동 재배포가 완료됩니다.
echo ========================================================
echo.
pause
