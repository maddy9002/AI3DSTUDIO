import sys
import platform

print("================================")
print("AI3D Studio Environment Check")
print("================================")

print("\nPython Executable:")
print(sys.executable)

print("\nPython Version:")
print(sys.version)

print("\nArchitecture:")
print(platform.architecture())

print("\nTrying to import MediaPipe...")

try:
    import mediapipe as mp

    print("\nMediaPipe Imported Successfully")
    print("Version:", mp.__version__)

    print("\nMediaPipe Location:")
    print(mp.__file__)

    print("\nMediaPipe Contents:")
    print(dir(mp))

except Exception as e:

    print("\nMediaPipe Import Failed")
    print(type(e).__name__)
    print(e)

print("\n================================")
print("Environment Check Complete")
print("================================")