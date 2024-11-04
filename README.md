# The Cistern

A thrilling action-adventure game built with Python and the Arcade library. Navigate through mysterious levels, battle ghosts, and uncover the secrets hidden within **The Cistern**.

![Game Screenshot](assets/screenshots/game_screenshot.png)

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Linux](#linux)
- [Running the Game](#running-the-game)
- [Controls](#controls)
- [Troubleshooting](#troubleshooting)
- [Credits](#credits)
- [License](#license)

## Features

- **Engaging Gameplay**: Battle against ghosts and bosses in an immersive environment.
- **Stunning Graphics**: Beautiful visuals powered by the Arcade library.
- **Cross-Platform Support**: Play on Windows, macOS, or Linux.
- **Dynamic Soundtrack**: Enjoy an original soundtrack that adapts to the gameplay.
- **Challenging Levels**: Progress through increasingly difficult levels with unique challenges.

## Requirements

- **Python**: Version 3.7 or higher
- **Libraries**:
  - `arcade`
  - `pyglet`
  - `numpy`
- **Optional Libraries** (if applicable):
  - Any other libraries specified in `requirements.txt`

## Installation

### Windows

1. **Install Python 3.7 or Higher**

   - Download and install Python from the [official website](https://www.python.org/downloads/windows/).
   - During installation, ensure that you check the option **"Add Python to PATH"**.

2. **Install Git (Optional)**

   - If you wish to clone the repository using Git, download and install Git from [git-scm.com](https://git-scm.com/download/win).

3. **Clone or Download the Repository**

   - **Clone with Git**:

     ~ git clone https://github.com/Phineas/the-cistern.git

   - **Or Download ZIP**:
     - Go to the [GitHub repository](https://github.com/Phineas/the-cistern).
     - Click on **Code** and select **Download ZIP**.
     - Extract the downloaded ZIP file.

4. **Install Required Libraries**

   Open Command Prompt and navigate to the project directory:

   ~ cd the-cistern

   Install the required libraries using `pip`:

   ~ pip install -r requirements.txt

   - If `requirements.txt` is not available, install the libraries individually:

     ~ pip install arcade pyglet numpy

### macOS

1. **Install Python 3.7 or Higher**

   - Install [Homebrew](https://brew.sh/) if not already installed:

     ~ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

   - Install Python:

     ~ brew install python

2. **Install Git (Optional)**

   - Install Git via Homebrew:

     ~ brew install git

3. **Clone or Download the Repository**

   - **Clone with Git**:

     ~ git clone https://github.com/Phineas/the-cistern.git

   - **Or Download ZIP**:
     - Visit the [GitHub repository](https://github.com/Phineas/the-cistern).
     - Click **Code** and choose **Download ZIP**.
     - Unzip the downloaded file.

4. **Install Required Libraries**

   Open Terminal and navigate to the project directory:

   ~ cd the-cistern

   Install the libraries:

   ~ pip3 install -r requirements.txt

   - Or individually:

     ~ pip3 install arcade pyglet numpy

### Linux

1. **Install Python 3.7 or Higher**

   - **Debian/Ubuntu**:

     ~ sudo apt update

     ~ sudo apt install python3 python3-pip

   - **Fedora**:

     ~ sudo dnf install python3 python3-pip

   - **Arch Linux**:

     ~ sudo pacman -S python

2. **Clone or Download the Repository**

   - **Clone with Git**:

     ~ git clone https://github.com/Phineas/the-cistern.git

   - **Or Download ZIP**:
     - Go to the [GitHub repository](https://github.com/Phineas/the-cistern).
     - Click **Code** and select **Download ZIP**.
     - Extract the ZIP file.

3. **Install Required Libraries**

   Open Terminal and navigate to the project directory:

   ~ cd the-cistern

   **For Debian/Ubuntu and Fedora**, install the libraries using `pip3`:

   ~ pip3 install -r requirements.txt

   - Or individually:

     ~ pip3 install arcade pyglet numpy

   **For Arch Linux**, install the libraries using `pacman`:

   ~ sudo pacman -S python-arcade python-pyglet python-numpy

   - If any of these packages are not available in the official repositories, you can install them via the Arch User Repository (AUR) using an AUR helper like `yay`:

     Then, install the packages:

     ~ yay -S python-arcade python-pyglet python-numpy

   - Alternatively, you can use `pip` (not recommended on Arch Linux):

     ~ pip install --user arcade pyglet numpy

     - Note: Using `pip` with the `--user` flag installs packages for your user only, avoiding system-wide changes.

## Running the Game

1. **Navigate to the Project Directory**

   Ensure you are in the project's root directory:

   ~ cd the-cistern

2. **Run the Game**

   - **Windows**:

     ~ python main.py

   - **macOS/Linux**:

     ~ python3 main.py

   If you encounter a `ModuleNotFoundError`, ensure all libraries are installed and use the correct Python version.

## Controls

- **Movement**: Arrow Keys
- **Attack**: Hold **C** key to charge and release to attack
- **Walk/Run Toggle**: Hold **Shift** to walk
- **Restart Game**: Press **X** after game over
- **Debug Mode**: Press **D** to toggle debug information

## Troubleshooting

- **Import Errors**: If you receive errors about missing modules, double-check that all libraries are installed using the correct version of `pip`, `pip3`, or your package manager.

- **Python Version Issues**: Ensure you're using Python 3.7 or higher. Check your Python version with:

  ~ python --version

- **Permission Errors on macOS**: If macOS blocks the application, go to **System Preferences > Security & Privacy** and allow the app to run.

- **Arcade Library Issues**: If you experience problems with the Arcade library, refer to the [Arcade documentation](https://api.arcade.academy/en/latest/install/index.html) for platform-specific installation guides.

## Credits

- **Developer**: [Phineas](https://github.com/phowell212/)
- **Libraries**:
  - [Arcade](https://api.arcade.academy/)
  - [Pyglet](https://pyglet.readthedocs.io/en/latest/)
  - [NumPy](https://numpy.org/)
- **Assets**: All game assets are credited to their respective creators.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Enjoy playing The Cistern! If you encounter any issues or have suggestions, feel free to open an issue on the [GitHub repository](https://github.com/Phineas/the-cistern/issues).**
