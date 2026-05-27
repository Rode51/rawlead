' RawLead Legacy — пульт + radar_control :18765 (без окна консоли)
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
batPath = scriptDir & "\start-radar-desktop.bat"
If Not fso.FileExists(batPath) Then
  MsgBox "Не найден: " & batPath, vbCritical, "RawLead Legacy"
  WScript.Quit 1
End If
sh.Run "cmd /c """ & batPath & """", 0, False
