@echo off
cls
cd /d "F:\ImperYo Sport Casa\ImperYo 1\Programa de gestion Imperyo sport\Imperyo_app_9-7 - 2"

echo 🛠️ Resolviendo conflicto en app.py (usando versión NUEVA)...
powershell -Command "(Get-Content app.py) -replace '(?s)<<<<<<< HEAD.*?=======\r?\n', '' | Set-Content app.py"
powershell -Command "(Get-Content app.py) -replace '(?s)>>>>>>> temp_branch.*', '' | Set-Content app.py"

echo.
echo ✅ Conflicto resuelto. Añadiendo archivo...
git add app.py

echo.
echo 💾 Completando merge...
git commit -m "Resolver conflicto de merge en app.py"

echo.
echo 🚀 Subiendo a GitHub (forzado)...
git push origin main --force-with-lease

if %errorlevel% == 0 (
    echo ✅ ¡CONFLICTO RESUELTO Y CAMBIOS SUBIDOS!
    echo 🌐 Visita: https://github.com/LuisPastorMartinez/imperyo_app
) else (
    echo ❌ ERROR al subir.
    echo 💡 Revisa manualmente app.py y vuelve a intentar.
)

pause