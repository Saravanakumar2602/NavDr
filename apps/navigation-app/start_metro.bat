@echo off
cd /d "C:\navapp"
set PATH=C:\Program Files\nodejs;C:\Windows\System32;C:\Users\sarav\AppData\Local\Android\Sdk\platform-tools;%PATH%
npx expo start --localhost --port 8081 --clear
