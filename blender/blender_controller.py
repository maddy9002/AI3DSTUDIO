import subprocess

BLENDER_PATH = r"D:\BLENDER_FILES\blender.exe"

SCRIPT_PATH = r"C:\Users\dell\OneDrive\Desktop\AI3DSTUDIO\blender\create_glider.py"


def create_glider():

    subprocess.Popen([
        BLENDER_PATH,
        "--python",
        SCRIPT_PATH
    ])