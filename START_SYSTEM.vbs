Option Explicit

Dim objShell, objFSO
Dim workspaceDir, venvPath, pythonExe, streamlitExe
Dim apiCommand, streamlitCommand
Dim currentDir

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

currentDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
workspaceDir = currentDir

venvPath = workspaceDir & "\venv\Scripts"
pythonExe = venvPath & "\python.exe"
streamlitExe = venvPath & "\streamlit.exe"

If Not objFSO.FolderExists(venvPath) Then
    MsgBox "Virtual environment not found! Please run installation first.", vbCritical, "NCCR Platform"
    WScript.Quit
End If

If Not objFSO.FileExists(pythonExe) Then
    MsgBox "Python not found in virtual environment!", vbCritical, "NCCR Platform"
    WScript.Quit
End If

If Not objFSO.FileExists(workspaceDir & "\main.py") Then
    MsgBox "main.py not found!", vbCritical, "NCCR Platform"
    WScript.Quit
End If

If Not objFSO.FileExists(workspaceDir & "\app_streamlit.py") Then
    MsgBox "app_streamlit.py not found!", vbCritical, "NCCR Platform"
    WScript.Quit
End If

apiCommand = "cmd.exe /c cd /d """ & workspaceDir & """ && """ & pythonExe & """ main.py"
streamlitCommand = "cmd.exe /c cd /d """ & workspaceDir & """ && """ & streamlitExe & """ run app_streamlit.py"

objShell.Run apiCommand, 0, False

WScript.Sleep 3000

objShell.Run streamlitCommand, 0, False

Set objShell = Nothing
Set objFSO = Nothing
