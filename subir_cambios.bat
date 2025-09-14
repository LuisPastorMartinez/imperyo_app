@echo off
cls
cd /d "F:\ImperYo Sport Casa\ImperYo 1\Programa de gestion Imperyo sport\Imperyo_app_9-7 - 2"

echo 🔄 Sincronizando con GitHub...
git pull origin main --rebase 2>nul

if %errorlevel% neq 0 (
    echo ⚠️ Intentando integrar historias no relacionadas...
    git pull origin main --allow-unrelated-histories 2>nul
)

echo 📤 Añadiendo TODOS los cambios...
git add --all

REM Verificar si hay cambios para commitear
git diff --cached --quiet
if %errorlevel% equ 0 (
    echo ⚠️ No hay cambios nuevos para subir.
    pause
    exit /b 0
)

set /p MENSAJE="📝 Escribe un mensaje: "
if "%MENSAJE%"=="" set MENSAJE="Actualización rápida"

git commit -m "%MENSAJE%"

echo 🚀 Subiendo...
git push origin main

if %errorlevel% == 0 (
    echo ✅ ¡TODO SUBIDO! Visita: https://github.com/LuisPastorMartinez/imperyo_app
    echo 💡 Recuerda reiniciar Streamlit Cloud manualmente.
) else (
    echo ❌ ERROR al subir. Posibles causas:
    echo - Secretos detectados (.json, .env, etc.)
    echo - Historial desincronizado
    echo.
    echo 💡 Solución rápida:
    echo 1. git rm --cached .streamlit/*.json
    echo 2. git add .gitignore
    echo 3. git commit -m "Ignorar secretos"
    echo 4. git push origin main
)

pause