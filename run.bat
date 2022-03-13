@echo off

CD src
CMD /C "python -m cli %*"
CD ..
