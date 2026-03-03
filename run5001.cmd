@echo off
cd /d c:\Users\TI01\Documents\Sistema
.\.venv\Scripts\python.exe -c "import app; app.init_db(); app.app.run(host='127.0.0.1', port=5001, debug=False)"
