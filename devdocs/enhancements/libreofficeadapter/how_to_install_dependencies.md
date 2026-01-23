# LibreOffice UNO API — Installation Guide

Step-by-step guide to install LibreOffice and PyUNO for programmatic document manipulation.

---

## Overview

| Component | Purpose |
|-----------|---------|
| **LibreOffice** | The office suite (runs as a server) |
| **PyUNO** | Python bridge to control LibreOffice |
| **uno** | Python module that comes with LibreOffice |

---

## macOS

### Step 1: Install LibreOffice

```bash
# Option A: Homebrew (recommended)
brew install --cask libreoffice

# Option B: Download from website
# https://www.libreoffice.org/download/download/
```

### Step 2: Locate LibreOffice Python

LibreOffice bundles its own Python with UNO. Find it:

```bash
# Homebrew installation
/Applications/LibreOffice.app/Contents/Resources/python

# Verify
/Applications/LibreOffice.app/Contents/Resources/python --version
```

### Step 3: Link UNO to Your Python (Option A — Symlink)

```bash
# Find your Python's site-packages
python -c "import site; print(site.getsitepackages()[0])"
# Example: /Users/you/.pyenv/versions/3.11.0/lib/python3.11/site-packages

# Create symlinks
SITE_PACKAGES="/Users/you/.pyenv/versions/3.11.0/lib/python3.11/site-packages"
LO_PATH="/Applications/LibreOffice.app/Contents/Frameworks"

ln -s "$LO_PATH/LibreOfficePython.framework/Versions/Current/lib/python3.*/site-packages/uno.py" "$SITE_PACKAGES/"
ln -s "$LO_PATH/LibreOfficePython.framework/Versions/Current/lib/python3.*/site-packages/unohelper.py" "$SITE_PACKAGES/"
```

### Step 3: Use LibreOffice's Python Directly (Option B — Recommended)

Instead of linking, use LibreOffice's bundled Python:

```bash
# Create alias
alias lopython='/Applications/LibreOffice.app/Contents/Resources/python'

# Run your script with LibreOffice's Python
lopython your_script.py
```

Or in your project, specify the interpreter:

```bash
/Applications/LibreOffice.app/Contents/Resources/python -m pip install your-dependencies
```

### Step 4: Verify Installation

```python
# test_uno.py
try:
    import uno
    from com.sun.star.beans import PropertyValue
    print("UNO imported successfully!")
except ImportError as e:
    print(f"Failed to import UNO: {e}")
```

```bash
/Applications/LibreOffice.app/Contents/Resources/python test_uno.py
```

---

## Ubuntu / Debian

### Step 1: Install LibreOffice

```bash
sudo apt update
sudo apt install libreoffice
```

### Step 2: Install Python UNO Bridge

```bash
# Install the Python-UNO bridge package
sudo apt install python3-uno
```

### Step 3: Verify Installation

```bash
python3 -c "import uno; print('UNO OK')"
```

If you get an import error, check that you're using the system Python (not a venv):

```bash
# UNO is installed for system Python
/usr/bin/python3 -c "import uno; print('UNO OK')"
```

### Step 4: Using with Virtual Environment

UNO doesn't install via pip. To use it in a venv:

```bash
# Option A: Create venv with system packages
python3 -m venv --system-site-packages myenv
source myenv/bin/activate
python -c "import uno; print('UNO OK')"

# Option B: Symlink into venv
VENV_SITE=$(python -c "import site; print(site.getsitepackages()[0])")
ln -s /usr/lib/python3/dist-packages/uno.py "$VENV_SITE/"
ln -s /usr/lib/python3/dist-packages/unohelper.py "$VENV_SITE/"
```

---

## Docker

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install LibreOffice and Python UNO bridge
RUN apt-get update && apt-get install -y \
    libreoffice \
    python3-uno \
    && rm -rf /var/lib/apt/lists/*

# Install common fonts
RUN apt-get update && apt-get install -y \
    fonts-liberation \
    fonts-dejavu-core \
    fonts-noto \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for UNO in Python path
RUN PYTHON_SITE=$(python -c "import site; print(site.getsitepackages()[0])") && \
    ln -s /usr/lib/python3/dist-packages/uno.py "$PYTHON_SITE/" && \
    ln -s /usr/lib/python3/dist-packages/unohelper.py "$PYTHON_SITE/"

WORKDIR /app
COPY . .

# Verify UNO works
RUN python -c "import uno; print('UNO OK')"
```

### Docker Compose (with LibreOffice server)

```yaml
version: '3.8'

services:
  libreoffice:
    image: libreoffice/libreoffice:latest
    command: --headless --accept="socket,host=0.0.0.0,port=2002;urp;"
    ports:
      - "2002:2002"

  app:
    build: .
    depends_on:
      - libreoffice
    environment:
      - LIBREOFFICE_HOST=libreoffice
      - LIBREOFFICE_PORT=2002
```

---

## Starting LibreOffice as a Server

To use UNO API, LibreOffice must run as a background server:

### Start Manually

```bash
# macOS
/Applications/LibreOffice.app/Contents/MacOS/soffice \
    --headless \
    --accept="socket,host=localhost,port=2002;urp;StarOffice.ServiceManager"

# Linux
soffice --headless --accept="socket,host=localhost,port=2002;urp;StarOffice.ServiceManager"
```

### Start in Background

```bash
# macOS / Linux
nohup soffice --headless --accept="socket,host=localhost,port=2002;urp;" &

# Check it's running
lsof -i :2002
```

### As a systemd Service (Linux)

```ini
# /etc/systemd/system/libreoffice.service
[Unit]
Description=LibreOffice Headless Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/soffice --headless --accept="socket,host=127.0.0.1,port=2002;urp;"
Restart=always
User=libreoffice

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable libreoffice
sudo systemctl start libreoffice
```

---

## Connecting to LibreOffice from Python

```python
import uno
from com.sun.star.beans import PropertyValue

def connect_to_libreoffice(host="localhost", port=2002):
    """Connect to a running LibreOffice instance."""
    local_context = uno.getComponentContext()
    resolver = local_context.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local_context
    )

    try:
        ctx = resolver.resolve(
            f"uno:socket,host={host},port={port};urp;StarOffice.ComponentContext"
        )
        smgr = ctx.ServiceManager
        desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
        return desktop
    except Exception as e:
        raise ConnectionError(f"Cannot connect to LibreOffice at {host}:{port}: {e}")


# Usage
desktop = connect_to_libreoffice()
print("Connected to LibreOffice!")
```

---

## Verify Full Setup

```python
# full_test.py
import uno
from com.sun.star.beans import PropertyValue

def test_libreoffice():
    # 1. Connect
    local_context = uno.getComponentContext()
    resolver = local_context.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local_context
    )
    ctx = resolver.resolve(
        "uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext"
    )
    smgr = ctx.ServiceManager
    desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)

    print("✓ Connected to LibreOffice")

    # 2. Open a document
    doc = desktop.loadComponentFromURL(
        "file:///path/to/test.pptx",
        "_blank",
        0,
        ()
    )
    print(f"✓ Opened document: {doc.Title}")

    # 3. Access slides
    slides = doc.getDrawPages()
    print(f"✓ Found {slides.getCount()} slides")

    # 4. Close
    doc.close(True)
    print("✓ Closed document")

    print("\n All tests passed!")

if __name__ == "__main__":
    test_libreoffice()
```

```bash
# First, start LibreOffice server in another terminal
soffice --headless --accept="socket,host=localhost,port=2002;urp;"

# Then run test
python full_test.py
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'uno'` | Use LibreOffice's Python or create symlinks |
| `ConnectionRefusedError` | Start LibreOffice server first |
| `NoConnectException` | Check host/port, firewall settings |
| Fonts look wrong | Install fonts package (fonts-liberation, etc.) |
| Slow first connection | Normal — LibreOffice takes a few seconds to start |
| Memory issues | Restart LibreOffice server periodically |

---

## Summary

| Platform | Install LibreOffice | Install PyUNO |
|----------|---------------------|---------------|
| macOS | `brew install --cask libreoffice` | Use LO's bundled Python or symlink |
| Ubuntu | `apt install libreoffice` | `apt install python3-uno` |
| Docker | `apt install libreoffice python3-uno` | Symlink to app Python |

**Key points:**
1. LibreOffice must be installed
2. PyUNO comes with LibreOffice (not pip installable)
3. LibreOffice must run as a server for UNO connections
4. Use `--system-site-packages` for venvs or symlink uno.py
