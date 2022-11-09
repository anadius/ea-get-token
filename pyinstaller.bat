@echo off

python -m PyInstaller ^
    --noupx ^
    --noconfirm ^
    --log-level=WARN ^
    --onefile ^
    --console ^
    --clean ^
    --name get_token ^
    --icon=NONE ^
    get_token.py

rmdir /s /q build
del get_token.spec
