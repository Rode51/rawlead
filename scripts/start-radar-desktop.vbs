' FL Radar — запуск пульта без окна консоли (ярлык на этот файл).
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
batPath = scriptDir & "\start-radar-desktop.bat"
If Not fso.FileExists(batPath) Then
  MsgBox "Не найден: " & batPath, vbCritical, "FL Radar"
  WScript.Quit 1
End If
sh.Run "cmd /c """ & batPath & """", 0, False
