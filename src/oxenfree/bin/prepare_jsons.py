#!/usr/bin/env python3
import csv
import logging

from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import Iterable

from oxenfree import (
    TranslationEntry,
    TranslationMap,
    TranslationScene,
)

logger = logging.getLogger(__name__)


@dataclass
class Args:
    debug: bool
    csv: Path
    output_dir: Path


def parse_args() -> Args:
    p = ArgumentParser(description='script to prepare JSON files for translation and repacking')
    p.add_argument('--csv', required=True, type=Path,
        help='original csv to derive data from')
    p.add_argument('--output-dir', type=Path, default='output/prepare_jsons/',
        help='where to put resulting JSONs')
    p.add_argument('--debug', action='store_true',
        help='print more logs')
    return Args(**p.parse_args().__dict__)


def main(args: Args) -> None:
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    csvfile = read_file(args.csv)
    entries_map = csv_to_map(csvfile)
    dump_map(entries_map, args.output_dir)


def read_file(filepath: Path) -> Iterable[Iterable[str]]:
    logger.info(f'opening {filepath}')
    if not filepath.is_file():
        raise RuntimeError(f'{filepath} is not a file')

    with filepath.open(encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')

        for line in reader:
            yield line


def tag_to_scene(tag: str) -> str:
    '''>>> tag_to_scene('A1S1.ENTLIG_RILEY_0000')
    A1S1.ENTLIG
    '''
    first, second, *_ = tag.split('_', maxsplit=2)
    if '.' in first:
        # name like A2W2.WADWAT
        return first
    # name like A2W2_01CONV
    return f'{first}_{second}'


def csv_to_map(csvfile: Iterable[Iterable[str]]) -> TranslationMap:
    logger.info('converting csv to translation map')
    result: TranslationMap = dict()
    for csv_entry in csvfile:
        tag, bundle, en, ru, uk = csv_entry
        if tag == 'tag':
            # first line with headers
            continue
        logger.debug(f'csv_to_map: {tag}')
        scene = tag_to_scene(tag)
        if scene not in result:
            result[scene] = TranslationScene(bundle, scene, [])
        trans_entry = TranslationEntry(
            tag=tag,
            en=en,
            ru_native=ru,
            ru_machine='',
            ru_final='',
            verified=False,
            uk=uk,
        )
        if 'DO NOT DELETE' in en:
            # verify choice stubs automatically
            trans_entry.ru_final = en
            trans_entry.verified = True
        result[scene].entries.append(trans_entry)
    logger.info('conversion done')
    return result


def dump_map(entries_map: TranslationMap, output_dir: Path) -> None:
    logger.info(f'saving translation map into {output_dir.absolute()}')
    if output_dir.is_dir():
        logger.info(f'directory {output_dir} exists; cleanup')
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for scene_name, scene in entries_map.items():
        scene.save_to_file(output_dir)
    logger.info('saving done')


def _main() -> None:
    main(parse_args())


if __name__ == '__main__':
    _main()
