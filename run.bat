@echo off
echo [1/2] Refreshing deal engine...
python -m dealengine.check --write

echo [2/2] Starting website preview...
cd site
npm run dev
pause
