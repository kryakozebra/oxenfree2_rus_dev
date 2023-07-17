#!/usr/bin/env python3

import csv
import logging
import os
import shutil

from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import UnityPy

from oxenfree.bundle import detect_bundle_dir, get_text_tree


logger = logging.getLogger(__name__)
if UnityPy.__version__ != '1.9.10':
    logger.warning(f'UnityPy {UnityPy.__version__} detected, but only 1.9.10 was tested!')


@dataclass
class Args:
    debug: bool
    game_dir: Path
    output_dir: Path
    required_bundles: List[str]

TextMap = Dict[str, Dict[str, str]]

def parse_args() -> Args:
    p = ArgumentParser()
    p.add_argument('--game-dir', required=True, type=Path,
        help='Oxenfree 2 directory, containing .exe, or StandaloneWindows64 subdir inside StreamingAssets')
    p.add_argument('--output-dir', type=Path, default='output/unpack_bundle/',
        help='directory where to put text table')
    p.add_argument('--required-bundles', nargs='+', type=Path, default=[
        'dialogue_packages_assets_all',
        'loc_packages_assets_',
    ], help='.bundle files to be unpacked; if none - unpack everything')
    p.add_argument('--debug', action='store_true',
        help='print more logs')
    return Args(**p.parse_args().__dict__)


def main(args: Args) -> None:
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    bundles = get_bundles(args.game_dir, args.required_bundles)
    text_map = upy_unpack_bundles(bundles)
    dump_text_map(text_map, args.output_dir)


def get_bundles(game_dir: Path, required_bundles: List[str]) -> Dict[str, Path]:
    logger.info('collecting bundle paths')
    result = dict()

    bundle_dir = detect_bundle_dir(game_dir)

    for file in bundle_dir.iterdir():
        logger.debug(f'bundles: check if {file} valid')
        if not file_is_valid_bundle(file, required_bundles):
            continue
        logger.debug(f'bundles: use {file}')

        name, _ = os.path.splitext(file.name)
        result[f'{name}.dir'] = file
    return result


def file_is_valid_bundle(filename: Path, bundles: List[str]) -> bool:
    if not filename.is_file():
        return False
    name, ext = os.path.splitext(filename.name)
    if ext != '.bundle':
        return False
    if not bundles:
        return True
    return name in bundles


def upy_unpack_bundles(bundles: Dict[str, Path]) -> TextMap:
    logger.info('unpacking bundles...')
    text_map: TextMap = dict()
    for key, bundle in bundles.items():
        logger.info(f'loading bundle {key}...')
        env = UnityPy.load(str(bundle))
        logger.info('loading completed; extracting MonoBehaviours now...')

        # iterate over internal objects
        for obj in env.objects:
            tree = get_text_tree(obj)
            if not tree:
                continue
            fill_text_map(
                tree,
                os.path.splitext(bundle.name)[0],
                text_map,
            )
    logger.info('unpacking done')
    return text_map


def fill_text_map(tree: Dict[str, Any], bundle: str, text_map: TextMap) -> None:
    obj_name = tree['m_Name']
    logger.debug(f'fill: {obj_name}')
    lang = tree['_ietfTag']
    if lang not in ['en', 'ru', 'uk']:
        logger.debug(f'fill: skip {obj_name}, useless language {lang}')
        return
    for e in tree['_database']['_entries']:
        tag = e['_entryName']
        if not tag in text_map:
            text_map[tag] = dict()
        tm = text_map[tag]
        if tm.get(lang):
            logger.warning(f'fill: {tag}-{lang} already exists!!')
        tm[lang] = e['_localization']
        tm['bundle'] = bundle


def dump_text_map(text_map: TextMap, output_dir: Path) -> None:
    csv_file = output_dir / 'text_table.csv'
    logger.info(f'writing text table to {csv_file}...')
    if output_dir.is_dir():
        logger.info(f'directory {output_dir} exists; cleanup')
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with csv_file.open('w', encoding='utf-8', newline='\n') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['tag', 'bundle', 'en', 'ru', 'uk'])

        items = list(text_map.items())
        items.sort(key=lambda x: x[0])

        for tag, data in items:
            line = [
                tag,
                data['bundle'],
                data.get('en', '<none>'),
                data.get('ru', '<none>'),
                data.get('uk', '<none>'),
            ]
            writer.writerow(line)
    logger.info('writing done')


def _main() -> None:
    main(parse_args())


if __name__ == '__main__':
    _main()
