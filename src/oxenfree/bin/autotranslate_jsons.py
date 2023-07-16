#!/usr/bin/env python3

import logging
import shutil
import time

from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
from typing import List

import deepl

from oxenfree import (
    TranslationEntry,
    TranslationMap,
    load_translation_map_from_dir,
)

logger = logging.getLogger(__name__)


@dataclass
class Args:
    debug: bool
    dialogue_bundle: bool
    translations_dir: Path
    output_dir: Path


def parse_args() -> Args:
    p = ArgumentParser(description='run Google Translate on every json that has english text and no'
        ' verified russian translation')
    p.add_argument('--translations-dir', required=True, type=Path,
        help='path to load translation JSONs from')
    p.add_argument('--output-dir', type=Path, default='output/autotranslate_jsons/',
        help='where to save updated JSONs')
    p.add_argument('--dialogue-bundle', action='store_true',
        help='translate even contents of dialogue_packages_assets_all, even though it is broken')
    p.add_argument('--debug', action='store_true',
        help='print more logs')
    return Args(**p.parse_args().__dict__)


def main(args: Args) -> None:
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    # silence verbose logger from googletrans
    logging.getLogger('hpack.hpack').setLevel(logging.INFO)
    logging.getLogger('httpx.client').setLevel(logging.INFO)
    # silence verbose logger from deepl
    logging.getLogger('urllib3.connectionpool').setLevel(logging.INFO)

    translation = get_translation_map(args.translations_dir)
    run_machine_translation(translation, args.output_dir, args.dialogue_bundle)


def get_translation_map(translations_dir: Path) -> TranslationMap:
    logger.info('loading translation JSONs...')
    result = load_translation_map_from_dir(translations_dir)
    logger.info('loading JSONs done')
    return result


def run_machine_translation(
        trans_map: TranslationMap, output_dir: Path,
        dialogue_bundle_too: bool
    ) -> None:
    logger.info('running machine translation...')

    if output_dir.is_dir():
        logger.info(f'directory {output_dir} exists; cleanup')
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for scene_key, scene in trans_map.items():
        translate_scene_entries(scene.entries)
        scene.save_to_file(output_dir)
    logger.info('translating done')


def translate_scene_entries(entries: List[TranslationEntry]) -> None:
    for e in entries:
        logger.debug(f'translate: {e.tag}')
        if e.ru_machine or e.ru_native or e.ru_final:
            logger.debug('translate: ru text exists')
            if e.ru_machine and not e.ru_machine.startswith('{D}'):
                e.ru_machine = '{D} ' + e.ru_machine
            continue
        if not e.en:
            logger.warning('translate: no en text')
            continue
        def trans() -> str:
            return '{D} ' + deepl.translate(
                source_language='EN',
                target_language='RU',
                text=e.en,
                formality_tone='informal'
            )
        try:
            e.ru_machine = trans()
        except Exception as ex:
            logger.exception(f'translation failed: {ex}')
            logger.info('sleep 30 seconds and hope for the best...')
            time.sleep(30)
            e.ru_machine = trans()
        logger.debug(f'translate: result: {e.ru_machine}')


def _main() -> None:
    main(parse_args())


if __name__ == '__main__':
    _main()
