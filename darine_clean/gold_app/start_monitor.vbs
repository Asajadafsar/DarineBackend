Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd.exe /c python manage.py check_prices", 0, False