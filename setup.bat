@ECHO off

SET destn=bin\2.0\dist

pyinstaller --distpath=%destn% MineGauler.spec

COPY /Y files\README.txt %destn%\README.txt
COPY /Y CHANGELOG.txt %destn%\CHANGELOG.txt

IF %1==--cli (
    pyinstaller --distpath=build\dist MineGaulerCLI.spec
    COPY /Y build\dist\MineGaulerCLI\MineGaulerCLI.exe %destn%\MineGauler\MineGaulerCLI.exe
    )
