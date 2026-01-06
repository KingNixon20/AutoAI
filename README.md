# AutoAI — Desktop Automation Builder

AutoAI is a GTK-based desktop application for creating, training, and running
desktop automation workflows on Linux. It provides a visual workflow editor,
image-class management for template matching, and an extensible driver layer
that can use `pyautogui`, `xdotool`, or other backends.

## Features (scaffold)

- GTK4 UI using `PyGObject`
- Create and manage projects and image-based classes
- Visual workflow editor (steps: Delay, FindAndClick, TypeText, KeyPress)
- Action settings panel and templates manager
- YAML-based workflow persistence in `projects/<project>/workflows`

## Quickstart

1. Create and activate a Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app

```bash
python3 -m app.main
```

## Project layout

- `app/` — GTK application and UI widgets
- `engine/` — driver interfaces and runtime manager
- `storage/` — project and workflow persistence (YAML)
- `projects/` — user projects (created at runtime)

## Saving workflows

Workflows are saved as YAML files in `projects/<project>/workflows/<project>.yaml`.

## Notes

- On Wayland some drivers (e.g., `xdotool`) may not work; use suitable backends.
- This repository is a scaffold — many features (runner, training pipeline,
  packaging) are planned but not yet implemented.

## Contributing

Pull requests and issues are welcome. Keep changes focused and include
tests for new functionality when possible.

## License

GNU 

see LICENSE
