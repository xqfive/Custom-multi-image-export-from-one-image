# Batch Image Selection Export Tool
Custom export of multiple images from a single picture
<img width="1202" height="886" alt="image" src="https://github.com/user-attachments/assets/3ec65b69-c5ce-4486-997d-321f73703f92" />


## Programming Language

**Python 3.x**

---

## Runtime Dependencies

| Library | Purpose |
|---------|---------|
| PyQt5 | GUI Framework |
| PIL (Pillow) | Image Processing |
| sys, os | System Operations |

### Install Dependencies

```bash
pip install PyQt5 Pillow
```

---

## Software Purpose

**Batch Image Selection Export Tool** (Version 1.4)

A desktop GUI application for creating selection regions on images and batch exporting cropped images.

---

## Main Features

| Feature | Description |
|---------|-------------|
| **Image Loading** | Load from file (`Ctrl+O`) or paste from clipboard (`Ctrl+Shift+V`) |
| **Shape Selection** | Supports square, rectangle, and circle shapes |
| **Size Preview** | Preview selection size effects |
| **Rounded Corners** | Rectangle and square support rounded corners |
| **Drag & Drop** | Drag shapes onto the canvas |
| **Batch Export** | Export all selections at once (`Ctrl+S`) |
| **Undo** | Undo add/delete selection operations |
| **Zoom** | `Ctrl+Scroll` to zoom canvas (10%-1000%) |
| **Fine Adjustment** | Use WASD keys to fine-tune selection position |

---

## Keyboard Shortcuts

| Shortcut | Function |
|----------|----------|
| `Esc` | Confirm exit |
| `Ctrl+O` | Open image |
| `Ctrl+Shift+V` | Paste image |
| `Ctrl+Q` | Clear image |
| `Ctrl+S` | Export all selections |
| `Ctrl+1` | Toggle square preview |
| `Ctrl+2` | Toggle rectangle preview |
| `Ctrl+3` | Toggle circle preview |
| `W` | Move selection up |
| `S` | Move selection down |
| `A` | Move selection left |
| `D` | Move selection right |

---

## Usage Guide

### 1. Launch the Application

```bash
python main.py
```

Or double-click `run.pyw` (runs without console window)

### 2. Load Image

- Click "Open Image" button or press `Ctrl+O`
- Or press `Ctrl+Shift+V` to paste from clipboard

### 3. Create Selection

- Set shape size in the left panel
- Check "Size Preview" to see the effect
- Drag shape onto the image, or double-click to add

### 4. Adjust Selection

- Click to select a region
- Drag edges to resize
- Drag center to move
- Use WASD keys for fine position adjustment

### 5. Export Images

- Set filename prefix
- Click "Export All Selections" or press `Ctrl+S`
- Images are saved to the `output` directory

---

## File Structure

| File | Description |
|------|-------------|
| `main.py` | Application entry point |
| `run.pyw` | Startup script without console |
| `config.py` | Global configuration |
| `main_window.py` | Main window UI |
| `shape_item.py` | Selection shape class |
| `shape_manager.py` | Shape manager |
| `image_processor.py` | Image processor |
| `custom_view.py` | Custom graphics view |
| `ico.png` | Application icon |

---

## Core Classes

### Config (config.py)
Configuration management class (Singleton pattern):
- Shape dimensions
- File prefix
- Save path
- Naming mode

### ImageCropperWindow (main_window.py)
Main window class, responsible for:
- UI construction
- Event handling
- User interaction

### ShapeManager (shape_manager.py)
Shape manager, responsible for:
- Shape creation
- Shape updates
- Operation history tracking

### ShapeItem (shape_item.py)
Selection shape class, inherits from QGraphicsRectItem:
- Supports dragging and selection
- Supports edge resizing
- Supports square, rectangle, and circle

### ImageProcessor (image_processor.py)
Image processor, responsible for:
- Image loading (file/clipboard)
- Shape cropping
- Batch export

### CustomGraphicsView (custom_view.py)
Custom view class:
- Supports Ctrl+Scroll zoom
- Supports shape drag & drop

---

## Export File Naming Rules

| Naming Mode | Format |
|-------------|--------|
| Prefix + Timestamp | `{prefix}_{timestamp}_{index}.png` |
| Prefix Only | `{prefix}_{index}.png` |

Default prefix: `v：cqxq05`

---

## Packaging

The application supports packaging with PyInstaller:

```bash
pyinstaller --onefile --windowed --icon=ico.png --add-data "ico.png;." run.pyw
```

---

## Version Information

- **Version**: 1.4
- **Author ID**: v：cqxq05

