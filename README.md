# AI3DSTUDIO

AI3DSTUDIO is a Python-based 3D editor designed to bring 3D modeling, object manipulation, hand tracking, and AI-assisted interactions together in one application.

The project aims to provide an interactive 3D design environment inspired by applications such as Blender, Unity, and Unreal Engine.

## Features

* **3D Viewport:** Interact with objects in a 3D environment.
* **3D Modeling:** Create and manipulate 3D objects.
* **Object Selection:** Select objects and interact with scene elements.
* **Transform Tools:** Move, rotate, and scale objects.
* **Hand Tracking:** Explore hands-free interaction.
* **AI-Assisted Interaction:** Integrate AI capabilities into the 3D design workflow.
* **Scene Management:** Organize objects and work with scenes.
* **Keyboard and Mouse Controls:** Interact with the editor using conventional input methods.

*Note: AI3DSTUDIO is under active development. Features and their availability may change between versions.*

## Requirements

Before installing AI3DSTUDIO, ensure you have the following:

* Windows 10 or later
* Python 3.11 (64-bit recommended)
* Git
* A compatible graphics environment
* A webcam for hand-tracking functionality
* Additional software or services for features that depend on them, such as MySQL and Ollama

Some features may require additional configuration.

## Installation

Follow these steps to set up AI3DSTUDIO on your computer.

### 1. Install Git and Python

Install Git and Python 3.11 (64-bit) if they are not already installed.

Verify your Python installation:

```powershell
python --version
```

The recommended version for this project is Python 3.11.

### 2. Clone the repository

Open PowerShell or a terminal and run:

```powershell
git clone https://github.com/maddy9002/AI3DSTUDIO.git
cd AI3DSTUDIO
```

### 3. Create a virtual environment

Create an isolated Python environment for the project's dependencies:

```powershell
py -3.11 -m venv venv311
```

### 4. Activate the virtual environment

Run:

```powershell
.\venv311\Scripts\Activate.ps1
```

After activation, your terminal should display `(venv311)`.

If PowerShell blocks the activation script, consult the official Python documentation for alternative activation methods.

### 5. Install the dependencies

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Install the required Python packages:

```powershell
python -m pip install -r requirements.txt
```

Wait for the installation to finish.

### 6. Verify the installation

Check for dependency conflicts:

```powershell
python -m pip check
```

If the dependencies are consistent, pip should report:

```text
No broken requirements found.
```

### 7. Launch AI3DSTUDIO

From the repository's root directory, run:

```powershell
python app/main.py
```

This is the main application launch command.

## Important Note for Readers

**The main application entry point is `app/main.py`.**

The following files in the repository root are not the main application entry point:

* `main_saved.py`
* `sample_main.py`

Do not use these files to launch the primary application. To start AI3DSTUDIO, use:

```powershell
python app/main.py
```

The project also contains other files with similar names for development or saved versions. The correct entry point for the application is `app/main.py`.

## Dependency Information

The `requirements.txt` file specifies the Python packages needed by AI3DSTUDIO.

The project currently specifies compatible versions of NumPy, OpenCV, and MediaPipe to reduce dependency conflicts.

The current dependency configuration includes:

* PySide6
* PyOpenGL
* NumPy
* OpenCV
* MediaPipe
* cvzone
* MySQL Connector/Python
* Ollama

Installing the Python dependencies does not automatically install or configure external services such as MySQL Server or Ollama. Features that depend on these services may require additional setup.

## Project Structure

The repository contains several directories and files responsible for different parts of the application.

| Directory or file  | Purpose                                                  |
| ------------------ | -------------------------------------------------------- |
| `app/`             | Main application code and supporting modules             |
| `app/main.py`      | Main application entry point                             |
| `requirements.txt` | Python dependency list                                   |
| `README.md`        | Project documentation                                    |
| `main_saved.py`    | Saved Python file; not the main application entry point  |
| `sample_main.py`   | Sample Python file; not the main application entry point |

Other project directories contain modules for the viewport, scene management, tools, AI functionality, and related systems.

## Development Status

AI3DSTUDIO is an actively developed project. New modeling capabilities, interaction methods, and AI-assisted features are being developed over time.

Some features may be incomplete or require additional configuration.

## Contributing

Developers interested in experimenting with AI3DSTUDIO can clone the repository, create a virtual environment, install the dependencies, and explore the source code.

Before submitting changes, test the affected functionality and verify that the application launches correctly.

## License

Please refer to the repository for licensing information.
