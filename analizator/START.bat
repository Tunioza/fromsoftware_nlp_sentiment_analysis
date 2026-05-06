@echo off
REM Sprawdzenie czy srodowisko istnieje
IF NOT EXIST "env\Scripts\activate.bat" (
    echo NIE ZNALEZIONO SRODOWISKA WIRTUALNEGO!
    echo Upewnij sie, ze wykonales krok 'PRZYGOTOWANIE SRODOWISKA' z instrukcji.
    echo.
    pause
    exit
)

REM Aktywacja srodowiska i uruchomienie skryptu
call env\Scripts\activate
python analizator.py

REM Zatrzymanie okna po zakonczeniu
echo.
echo Program zakonczyl dzialanie.
pause