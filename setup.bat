@ECHO off

SET base=%cd%
SET destn=bin\2.1\windows

pyinstaller --distpath=%destn% MineGauler.spec

COPY /Y files\README.txt %destn%\README.txt
COPY /Y CHANGELOG.txt %destn%\CHANGELOG.txt

REM IF %1==--cli (
REM     pyinstaller --distpath=build\dist MineGaulerCLI.spec
REM     COPY /Y build\dist\MineGaulerCLI\MineGaulerCLI.exe %destn%\MineGauler\MineGaulerCLI.exe
REM     )

echo Creating zip archive...
cd %destn%/..
python -c "from shutil import make_archive; make_archive('windows', 'zip', 'windows')"
cd %base%
echo Done.
