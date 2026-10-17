@echo off
set PATH=C:\Windows\System32;C:\Program Files\nodejs;C:\Program Files\Android\Android Studio\jbr\bin;C:\Users\sarav\AppData\Local\Android\Sdk\platform-tools;%PATH%
subst N: /D >nul 2>&1
subst N: "c:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\apps\navigation-app"
set NODE_PRESERVE_SYMLINKS=1
cd /d N:\android
node --print "require.resolve('react-native/package.json')"
subst N: /D >nul 2>&1
