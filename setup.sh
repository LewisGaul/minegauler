
@ECHO off

SET destn=bin/2.0/linux

pyinstaller --distpath=$destn MineGauler.spec

CP /Y files/README.txt $destn/README.txt
CP /Y CHANGELOG.txt $destn/CHANGELOG.txt

IF $1==--cli;
THEN (
    pyinstaller --distpath=build/dist MineGaulerCLI.spec
    CP /Y build/dist/MineGaulerCLI/MineGaulerCLI.exe $destn/MineGauler/MineGaulerCLI.exe
    )
