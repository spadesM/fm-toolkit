@echo off
chcp 65001 >nul
title FM27 Performans ve P-Core Hizlandirici
python "%~dp0fm27_boost.py" %*
pause
