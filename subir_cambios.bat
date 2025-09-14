@echo off
cls
cd /d "F:\ImperYo Sport Casa\ImperYo 1\Programa de gestion Imperyo sport\Imperyo_app_9-7 - 2"

echo 🔄 Sincronizando con GitHub...
git pull origin main --rebase 2>nul

echo 📤 Añadiendo cambios...
git add .

set /p MENSAJE="📝 Escribe un mensaje: "
if "%MENSAJE%"=="" set MENSAJE="Actualización rápida"

git commit -m "%MENSAJE%"

echo 🚀 Subiendo...
git push origin main

if %errorlevel% == 0 (
    echo ✅ ¡TODO SUBIDO! Visita: https://github.com/LuisPastorMartinez/imperyo_app
    echo 💡 Recuerda reiniciar Streamlit Cloud manualmente.
) else (
    echo ❌ ERROR. Revisa los mensajes.
)

pause