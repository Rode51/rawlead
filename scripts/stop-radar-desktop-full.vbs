' RawLead — полный стоп site + legacy (без окна консоли)
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
batPath = scriptDir & "\stop-radar-desktop-full.bat"
If Not fso.FileExists(batPath) Then
  MsgBox "Не найден: " & batPath, vbCritical, "RawLead — стоп"
  WScript.Quit 1
End If
sh.Run "cmd /c """ & batPath & """", 0, False
