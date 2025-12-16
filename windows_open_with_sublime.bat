@echo

echo "Bat shall run with administrator"

REG ADD "HKEY_LOCAL_MACHINE\SOFTWARE\Classes\*\shell\sublime" /ve /t REG_SZ /d ">Open with Sublime"

REG ADD "HKEY_LOCAL_MACHINE\SOFTWARE\Classes\*\shell\sublime\command" /ve /t REG_SZ /d "D:\....\sublime_text.exe %%1"

pause
