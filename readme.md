# death

Ever wanted to make your screen go crazy, but dont want to kill your PC?
Like famous GDI/bitbld trojans, like MEMZ!

## Features

- Error boxes appear everywhere and get faster
- Error icons appear on your screen
- Parts of your screen get copied to other parts to glitch it
- A tunnel effect inspired by the original visual style
- Stop at any time with `F7`
- Non-destructive: keeps effects visual only
- Native `pieces` screen distortion effect
- Tunnel/shrink visual effect using Win32 screen capture and blitting

## Requirements

- Windows 10 / Windows 11
- Python 3.11+ (or the installed Python version matching your build environment)
- `pybind11`
- `pygame`
- `Pillow`
- `keyboard`
- `tkinter` (included with standard Windows Python)
- Build tools for compiling native extensions (MSVC / Visual Studio Build Tools)

## Setup

### Recommended: `autosetup.bat`

1. Open PowerShell in the project folder.
2. Activate your virtual environment if you use one.
3. Run:

```powershell
.\autosetup.bat
```

That script will:

- use your local `.venv` automatically if it exists
- install `pybind11` if needed
- rebuild both native extensions
- create `pieces.pyd` and `invert.pyd` in the project root

### Manual setup

1. Install the required Python packages:

```powershell
pip install pybind11 pygame pillow keyboard
```

2. Build the native extensions:

```powershell
python setup.py build_ext --force
```

3. Copy the built `.pyd` files from the `build` folder into the project root and rename them to:

- `pieces.pyd`
- `invert.pyd`

## Usage

Run the main script from the repository root:

```powershell
python main.py
```

## Contributing

Contributions are welcome. The goal of this project is to make `death` a visual, staged desktop effect while keeping it non-destructive.

Please do not commit directly to the project. Open a pull request instead.

When contributing, please keep these goals in mind:

- keep effects visual only and immediatley undoable
- design for windows 10 and 11
- avoid unnecessary complexity when a simple approach fits the project better

Good contribution ideas:

- new visual effects or stage improvements
- bug fixes and performance improvements
- cleaner build/setup tooling

Suggested workflow:

1. Clone or fork the repository.
2. Build the project with `.\autosetup.bat`.
3. Make your changes in small, focused commits.
4. Rebuild the native modules after changing `pieces.cpp` or `invert.cpp`.
5. Test by running `python main.py` and confirming the affected behavior still works.
6. Push your branch and open a pull request for review instead of committing directly to the main project.
7. Update `readme.md` if your change affects setup, usage, or project structure.

If you touch native modules, please try to keep the Python-facing API stable unless there is a clear reason to change it. If you do change that API, update the matching `.pyi` stub files too.

Before opening a pull request, make sure:

- the project still builds cleanly
- `pieces.pyd` and `invert.pyd` can be regenerated successfully
- your change matches the goal of the project
- any user-facing behavior changes are documented

For bigger changes, it helps to describe the goal first and keep the scope clear. That makes review much easier and keeps the project moving without confusion.
