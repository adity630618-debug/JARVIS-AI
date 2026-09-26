import os
import sys

def enable_autostart():
    """
    Creates a startup script in the Windows Startup folder so
    J.A.R.V.I.S automatically boots up whenever the PC is turned on.
    """
    startup_folder = os.path.join(
        os.environ.get("APPDATA", ""),
        r"Microsoft\Windows\Start Menu\Programs\Startup"
    )

    if not os.path.exists(startup_folder):
        print(f"[Error] Could not find Windows Startup folder: {startup_folder}")
        return False

    jarvis_dir = os.path.abspath(os.path.dirname(__file__))
    bat_file = os.path.join(jarvis_dir, "run_jarvis.bat")

    # We use a small VBScript runner so it can launch smoothly on startup
    vbs_path = os.path.join(startup_folder, "Jarvis_AutoStart.vbs")
    
    vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "{jarvis_dir}"
WshShell.Run chr(34) & "{bat_file}" & chr(34), 1, False
'''
    try:
        with open(vbs_path, "w") as f:
            f.write(vbs_content)
        print("=" * 60)
        print("[SUCCESS] J.A.R.V.I.S has been added to Windows Startup!")
        print(f"File created: {vbs_path}")
        print("Now every time you start your PC, J.A.R.V.I.S will automatically wake up")
        print('and greet you: "Hello Sir, how are you? and how can I help you?"')
        print("=" * 60)
        return True
    except Exception as e:
        print(f"[Error] Failed to enable auto-start: {e}")
        return False

def disable_autostart():
    """Removes J.A.R.V.I.S from Windows Startup folder."""
    startup_folder = os.path.join(
        os.environ.get("APPDATA", ""),
        r"Microsoft\Windows\Start Menu\Programs\Startup"
    )
    vbs_path = os.path.join(startup_folder, "Jarvis_AutoStart.vbs")
    if os.path.exists(vbs_path):
        os.remove(vbs_path)
        print("[SUCCESS] J.A.R.V.I.S removed from Windows Startup.")
    else:
        print("[Info] J.A.R.V.I.S was not registered in Startup.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "disable":
        disable_autostart()
    else:
        enable_autostart()
