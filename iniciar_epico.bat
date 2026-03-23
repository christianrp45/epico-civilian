@echo off
title Plataforma EPICO
echo =========================================
echo    Iniciando a Plataforma EPICO...
echo    Aguarde, abrindo no navegador.
echo =========================================

:: Ativa o ambiente virtual automaticamente
call .venv\Scripts\activate

:: Roda o aplicativo
python -m streamlit run app.py

pause