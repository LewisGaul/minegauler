@ECHO off

SET destn=bin/2.0/dist

pyinstaller --distpath=%destn% MineGauler.spec

COPY /Y files/README.txt %destn%/README.txt
COPY /Y CHANGELOG.txt %destn%/CHANGELOG.txt
