#!/usr/bin/env python3

import logging

from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from oxenfree import (
    TranslationEntry,
    TranslationMap,
    load_translation_map_from_dir,
)

logger = logging.getLogger(__name__)


@dataclass
class Args:
    debug: bool
    list_untranslated: bool
    translations_dir: Path


def parse_args() -> Args:
    p = ArgumentParser(description='gather stats on JSONs in folder')
    p.add_argument('--translations-dir', required=True, type=Path,
        help='path to load translation JSONs from')
    p.add_argument('--list-untranslated', action='store_true',
        help='get list of untranslated tags')
    p.add_argument('--debug', action='store_true',
        help='print more logs')
    return Args(**p.parse_args().__dict__)


def main(args: Args) -> None:
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    translation = get_translation_map(args.translations_dir)

    entries: List[TranslationEntry] = []
    st_all_entries = 0
    st_en_entries = 0
    st_ru_entries = 0
    st_uk_entries = 0
    st_verified_entries = 0
    st_machine_entries = 0
    for scene_name, scene in translation.items():
        for e in scene.entries:
            entries.append(e)
            st_all_entries += 1
            if e.en:
                st_en_entries += 1
            if e.ru_native:
                st_ru_entries += 1
            if e.verified:
                st_verified_entries += 1
            if e.ru_machine:
                st_machine_entries += 1
            if e.uk:
                st_uk_entries += 1

    def percent(x: int, total: int=st_all_entries) -> int:
        return int(x / total * 100)
    st_untranslated_entries = st_all_entries - st_ru_entries
    print(f'Всего строк: {st_all_entries}')
    print(f'Непереведённых строк: {st_untranslated_entries}, {percent(st_untranslated_entries)}%')
    print(f'Оригинальных англ. строк: {st_en_entries}, {percent(st_en_entries)}%')
    print(f'Оригинальных укр. строк: {st_uk_entries}, {percent(st_uk_entries)}%')
    print(f'Оригинальных рус. строк: {st_ru_entries}, {percent(st_ru_entries)}%')
    print(f'Машинных рус. строк: {st_machine_entries}, {percent(st_machine_entries, st_untranslated_entries)}%')
    print(f'Подтверждённых рус. строк: {st_verified_entries}, {percent(st_verified_entries)}%')

    if args.list_untranslated:
        untranslated = (x for x in entries if not x.ru_final)
        for x in sorted(untranslated, key=lambda x: x.tag):
            print(x.tag)

def get_translation_map(translations_dir: Path) -> TranslationMap:
    logger.info('loading translation JSONs...')
    result = load_translation_map_from_dir(translations_dir)
    logger.info('loading JSONs done')
    return result


def _main() -> None:
    main(parse_args())

    
if __name__ == '__main__':
    _main()
