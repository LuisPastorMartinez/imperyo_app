@echo off
cls
cd /d "F:\ImperYo Sport Casa\ImperYo 1\Programa de gestion Imperyo sport\Imperyo_app_9-7 - 2"

echo 📁 Verificando ubicación...
if not exist "bfg-1.14.0.jar" (
    echo ❌ No se encontró bfg-1.14.0.jar
    echo 💡 Descárgalo desde: https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar
    echo 💡 Y colócalo en esta carpeta.
    pause
    exit /b 1
)

echo 🧹 Eliminando secreto del historial...
java -jar bfg-1.14.0.jar --delete-files imperyo-sport-app-a4535f8042c9.json

echo 🧹 Limpiando repositorio...
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo 🚀 Forzando push...
git push origin main --force-with-lease

if %errorlevel% == 0 (
    echo ✅ ¡ÉXITO! Historial limpio y cambios subidos.
    echo 🎉 Visita: https://github.com/LuisPastorMartinez/imperyo_app
) else (
    echo ❌ ERROR. Revisa los mensajes anteriores.
)

pause