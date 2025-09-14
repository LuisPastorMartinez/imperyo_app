@echo off
cls
echo.
echo 🚀 SUBIENDO CAMBIOS A GITHUB...
echo.

REM Navegar a tu carpeta del proyecto (¡CAMBIA ESTA RUTA POR LA TUYA!)
cd /d "F:\ImperYo Sport Casa\ImperYo 1\Programa de gestion Imperyo sport\Imperyo_app_9-7 - 2"

echo 1. Agregando todos los archivos modificados...
git add .

echo.
echo 2. Haciendo commit...
set /p MENSAJE="📝 Escribe un mensaje para este cambio (ej: 'Arreglé backup'): "
if "%MENSAJE%"=="" set MENSAJE="Actualización rápida"

git commit -m "%MENSAJE%"

echo.
echo 3. Subiendo a GitHub...
git push origin main

echo.
echo.
if %errorlevel% == 0 (
    echo ✅ ¡CAMBIOS SUBIDOS CON ÉXITO!
    echo.
    echo 🎉 Tu app en Streamlit Cloud se actualizará pronto.
    echo 💡 Recuerda reiniciarla manualmente si es necesario.
) else (
    echo ❌ ERROR al subir los cambios.
    echo.
    echo 🔍 Posibles causas:
    echo - No hay conexión a internet.
    echo - No has configurado tu email/nombre en Git.
    echo - Hay cambios en GitHub que no tienes localmente (haz "git pull" primero).
)

echo.
pause