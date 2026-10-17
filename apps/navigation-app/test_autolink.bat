@echo off
set PATH=C:\Windows\System32;C:\Program Files\nodejs;C:\Program Files\Android\Android Studio\jbr\bin;C:\Users\sarav\AppData\Local\Android\Sdk\platform-tools;%PATH%
set NODE_PRESERVE_SYMLINKS=1
subst S: /D >nul 2>&1
subst S: "c:\Saravanakumar G\Projects\SIH26\IO-VNBD-master"
cd /d S:\apps\navigation-app\android
call npx expo-modules-autolinking verify
echo EXIT CODE: %ERRORLEVEL%
subst S: /D >nul 2>&1
