@echo off
cls
cd /d "F:\ImperYo Sport Casa\ImperYo 1\Programa de gestion Imperyo sport\Imperyo_app_9-7 - 2"

echo 🔄 Cambiando a rama 'main'...
git checkout main

echo.
echo 🔄 Volviendo al commit b7acb25 (descartando cambios posteriores)...
git reset --hard b7acb25

echo.
echo 🚀 Subiendo a GitHub (forzado)...
git push origin main --force-with-lease

if %errorlevel% == 0 (
    echo ✅ ¡VUELTO A LA VERSIÓN b7acb25!
    echo 🌐 Visita: https://github.com/LuisPastorMartinez/imperyo_app
    echo.
    echo 💡 Reinicia Streamlit Cloud: "Manage app" → "Clear cache and redeploy"
) else (
    echo ❌ ERROR al subir.
    echo 💡 ¿Estás en la rama correcta? Ejecuta: git checkout main
)

pause