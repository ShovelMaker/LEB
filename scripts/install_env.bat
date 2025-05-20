@echo off
REM -- 가상환경 & 의존성 설치
python -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo ✅ Environment setup complete.
pause
