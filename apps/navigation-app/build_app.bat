@echo off
set PATH=C:\Windows\System32;C:\Program Files\nodejs;C:\Program Files\Android\Android Studio\jbr\bin;C:\Users\sarav\AppData\Local\Android\Sdk\platform-tools;%PATH%
if not exist "C:\navapp" mkdir "C:\navapp"
robocopy "c:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\apps\navigation-app" "C:\navapp" /MIR /XD node_modules .gradle .cxx build dist .expo /R:2 /W:1
cd /d "C:\navapp"
call npm install --legacy-peer-deps
cd /d "C:\navapp\android"
if exist "app\.cxx" rmdir /s /q "app\.cxx"
if exist ".gradle" rmdir /s /q ".gradle"
if exist "app\build" rmdir /s /q "app\build"
if exist "C:\tmp\cxx" rmdir /s /q "C:\tmp\cxx"
if exist "C:\tmp\b" rmdir /s /q "C:\tmp\b"
echo sdk.dir=C:\\Users\\sarav\\AppData\\Local\\Android\\Sdk> local.properties
echo ndk.dir=C:\\Users\\sarav\\AppData\\Local\\Android\\Sdk\\ndk\\27.1.12297006>> local.properties
set ANDROID_HOME=C:\Users\sarav\AppData\Local\Android\Sdk
set JAVA_HOME=C:\Program Files\Android\Android Studio\jbr
call gradlew.bat installDebug

