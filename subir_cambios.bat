@echo off
cls
cd /d "F:\ImperYo Sport Casa\ImperYo 1\Programa de gestion Imperyo sport\Imperyo_app_9_8-1"

echo 🛡️ VERIFICANDO ENTORNO...
git rev-parse --git-dir >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: Esta carpeta NO es un repositorio Git.
    echo 💡 Ejecuta primero: git init
    pause
    exit /b 1
)

echo.
echo 🔄 SINCRONIZANDO CON GITHUB...
git pull origin main --rebase 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ Intentando integrar historias no relacionadas...
    git pull origin main --allow-unrelated-histories 2>nul
)

echo.
echo 📤 AÑADIENDO CAMBIOS...
git add --all

REM Verificar si hay cambios para commitear
git diff --cached --quiet
if %errorlevel% equ 0 (
    echo ⚠️ No hay cambios nuevos para subir.
    pause
    exit /b 0
)

set /p MENSAJE="📝 Escribe un mensaje: "
if "%MENSAJE%"=="" set MENSAJE="Actualización automática"

git commit -m "%MENSAJE%"

echo.
echo 🚀 SUBIENDO A GITHUB...
git push origin main

if %errorlevel% == 0 (
    echo ✅ ¡CAMBIOS SUBIDOS CON ÉXITO!
    echo 🎉 Tu app en Streamlit Cloud se actualizará pronto.
    echo 💡 Recuerda reiniciarla manualmente si es necesario.
) else (
    echo ❌ ERROR al subir. Posibles causas:
    echo - Secretos detectados (.json, .env, etc.)
    echo - Conflictos no resueltos
    echo - Historial desincronizado
    echo.
    echo 💡 Solución rápida:
    echo 1. git rm --cached .streamlit/*.json
    echo 2. git add .gitignore
    echo 3. git commit -m "Ignorar secretos"
    echo 4. git push origin main
)

pause