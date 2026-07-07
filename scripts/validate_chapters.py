#!/usr/bin/env python3
import ast
import os
import re
import sys

STORY_DIR = os.path.join(os.path.dirname(__file__), '..', 'story')
ALLOWED_NEXT = {'chapter_end', 'next_chapter', 'game_end'}
errors = []

def load_chapter(path):
    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()
    try:
        ast.parse(src)
    except SyntaxError as e:
        return None, f"SyntaxError: {e}"
    ns = {}
    try:
        exec(compile(src, path, 'exec'), ns)
    except Exception as e:
        return None, f"Runtime error when importing: {e}"
    ch = None
    for k, v in ns.items():
        if k.startswith('CHAPTER_'):
            ch = v
            break
    if ch is None:
        return None, "No CHAPTER_* variable found"
    return ch, None


def validate_chapter_file(path):
    name = os.path.basename(path)
    ch, err = load_chapter(path)
    if err:
        errors.append((name, err))
        return
    title = ch.get('title')
    scenes = ch.get('scenes')
    if not title or not isinstance(scenes, dict):
        errors.append((name, 'Missing title or scenes dict'))
        return
    scene_names = set(scenes.keys())
    for sname, scene in scenes.items():
        if 'text' not in scene:
            errors.append((name, f"Scene '{sname}' missing text"))
        choices = scene.get('choices', [])
        for choice in choices:
            nxt = choice.get('next')
            if not nxt:
                errors.append((name, f"Scene '{sname}' has choice without next"))
            else:
                if nxt not in scene_names and nxt not in ALLOWED_NEXT:
                    errors.append((name, f"Scene '{sname}' has choice with unknown next '{nxt}'"))
            eff = choice.get('effect', {})
            if isinstance(eff, dict) and 'achievement' in eff and eff.get('achievement') == "":
                errors.append((name, f"Scene '{sname}' choice has empty achievement string"))


def main():
    story_dir = os.path.join(os.path.dirname(__file__), '..', 'story')
    files = sorted([f for f in os.listdir(story_dir) if re.match(r'chapter\d+\.py$', f)])
    for f in files:
        path = os.path.join(story_dir, f)
        validate_chapter_file(path)
    if errors:
        print('Validation completed with issues:')
        for name, msg in errors:
            print(f'- {name}: {msg}')
        sys.exit(2)
    print('All chapters validated successfully.')

if __name__ == '__main__':
    main()
