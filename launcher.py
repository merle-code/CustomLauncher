#!/usr/bin/python

import sys
import json
import os
import subprocess, shutil
from pprint import pprint as pp


from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw



DEFAULTS = {
    "base_dir": None,
    "extensions": [],
    "program": None,
    "args_template": "{file}",
    "icon": None,
    "name": "Launcher"
}

CONFIG = {}

def create_icon_image(icon_path):
    
    try:
        return Image.open(icon_path)
    except Exception:
        img = Image.new("RGBA", (64, 64), (30, 30, 30, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle((16, 16, 48, 48), fill=(0, 120, 255))
        return img


def run_file(program, path):

    if path and program:
        file_arg = CONFIG["args_template"].format(file=path)

        subprocess.Popen([program, file_arg])


def make_action(program, path):
    def action(icon, item):
        run_file(program, path)
    return action


def build_menu(node, program, config=None):
    items = []

    for key, value in sorted(node.items()):
        if key == "__files__":
            for name, file_path in value:
                item = MenuItem(name, make_action(program, file_path))
                items.append(item)
        else:
            items.append(
                MenuItem(
                    key,
                    build_menu(value, program)
                )
            )

    # root-only actions
    if config:
        items.append(Menu.SEPARATOR)
        items.append(MenuItem("Refresh", lambda i, _: on_refresh(i, _, config)))
        items.append(MenuItem("Exit", on_exit))

    return Menu(*items)


def rebuild_menu(icon, config):
    files = scan_files(config["base_dir"], config["extensions"])
    tree = build_tree(config["base_dir"], files)
    program = resolve_program(config["program"])

    icon.menu = build_menu(tree, program)


def print_tree(node, indent=0):
    for k, v in node.items():
        if k == "__files__":
            for name, _ in v:
                print("  " * indent + f"- {name}")
        else:
            print("  " * indent + f"[{k}]")
            print_tree(v, indent + 1)


def build_tree(base_dir, files):
    tree = {}

    for f in files:
        # relative path
        rel = os.path.relpath(f, base_dir)
        parts = rel.split(os.sep)

        node = tree

        # przechodzimy katalogi
        for part in parts[:-1]:
            node = node.setdefault(part, {})

        # pliki wrzucamy do __files__
        node.setdefault("__files__", []).append((
            os.path.splitext(parts[-1])[0],  # nazwa pliku
            f                                # pełna ścieżka
        ))

    return tree


def resolve_program(prog):
    # jeśli to pełna ścieżka i istnieje → użyj
    if os.path.isfile(prog):
        return prog

    # spróbuj znaleźć w PATH
    path = shutil.which(prog)
    if path:
        return path

    raise SystemExit(f"Program not found: {prog}")


def scan_files(base_dir, extensions):
    result = []

    # normalizacja ext (na wszelki wypadek)
    ext_set = {e.lower() for e in extensions} if extensions else None

    for root, _, files in os.walk(base_dir):
        for f in files:
            if ext_set:
                if not any(f.lower().endswith(ext) for ext in ext_set):
                    continue
            result.append(os.path.join(root, f))

    return sorted(result)


def load_config(path):
    if not os.path.isfile(path):
        raise SystemExit(f"Config not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # merge z defaultami
    for k, v in DEFAULTS.items():
        cfg.setdefault(k, v)

    # minimalna walidacja
    if not cfg["base_dir"]:
        raise SystemExit("Missing: base_dir")

    if not cfg["program"]:
        raise SystemExit("Missing: program")

    cfg["base_dir"] = os.path.abspath(cfg["base_dir"])

    if not os.path.isdir(cfg["base_dir"]):
        raise SystemExit(f"Invalid base_dir: {cfg['base_dir']}")

    return cfg


def on_exit(icon, item):
    icon.stop()


def on_refresh(icon, item, config):
    rebuild_menu(icon, config)


def main():

    global CONFIG
    if len(sys.argv) < 2:
        raise SystemExit("Usage: launcher.py <config.json>")

    config_path = sys.argv[1]
    CONFIG = load_config(config_path)

    # pierwszy build
    files = scan_files(CONFIG["base_dir"], CONFIG["extensions"])
    tree = build_tree(CONFIG["base_dir"], files)
    program = resolve_program(CONFIG["program"])

    #print_tree(tree)

    icon_image = create_icon_image(CONFIG["icon"])

    icon = Icon(CONFIG["name"])
    icon.icon = icon_image
    icon.title = CONFIG["name"]

    icon.menu = build_menu(tree, program, CONFIG)

    #pp(icon.menu)
    icon.run()


if __name__ == "__main__":
    main()
