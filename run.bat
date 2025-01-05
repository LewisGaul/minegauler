@echo off

CD src
CMD /C "python -m minegauler.app %*"
CD ..
