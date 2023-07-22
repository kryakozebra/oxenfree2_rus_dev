#!/usr/bin/env python3
import csv
import shutil
import logging

from argparse import ArgumentParser
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from oxenfree import (
    TranslationEntry,
    TranslationMap,
    TranslationScene,
    load_translation_map_from_dir,
)

logger = logging.getLogger(__name__)


@dataclass
class Args:
    debug: bool
    csv: List[Path]
    csv_format: str
    output_dir: Path
    patch: Optional[Path]
    force: bool


def parse_args() -> Args:
    p = ArgumentParser(description='script to prepare JSON files for translation and repacking')
    p.add_argument('--csv', required=True, type=Path, nargs='+',
        help='original CSV file(s) to derive data from')
    p.add_argument('--output-dir', type=Path, default='output/prepare_jsons/',
        help='where to put resulting JSONs')
    p.add_argument('--patch', type=Path,
        help='path to existing translation JSONs that should be patched')
    p.add_argument('--csv-format', required=True, choices=['lenferd', 'bundle'],
        help='where CSV files originate from\n'
        'lenferd - cooperative Google Sheet, maintained by Lenferd\n'
        'bundle - csv exported from bundle contects by unpack_bundle script\n')
    p.add_argument('--force', action='store_true',
        help='when patching, overwrite ru_final even if new value is identical to any of'
            ' existing translations')
    p.add_argument('--debug', action='store_true',
        help='print more logs')
    return Args(**p.parse_args().__dict__)


def main(args: Args) -> None:
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    entries = get_entries_from_csvs(args.csv, args.csv_format)
    if args.patch:
        real_map = load_translation_map_from_dir(args.patch)
        grouped_entries = apply_delta(real_map, entries, args.force)
    else:
        grouped_entries = group_entries(entries.values())

    dump_map(grouped_entries, args.output_dir)


@dataclass
class BundledTranslationEntry(TranslationEntry):
    bundle: str


def get_entries_from_csvs(csvs: List[Path], format: str) -> Dict[str, BundledTranslationEntry]:
    if format == 'lenferd':
        unpack = unpack_lenferd
    elif format == 'bundle':
        unpack = unpack_bundle
    else:
        # should not happen until someone f up with code
        raise NotImplementedError(f'invalid format {format}')
    pass

    result = dict()
    for file in csvs:
        for entry in unpack(file):
            if entry.tag in result:
                logger.warning(f'csv: {file} contains entry for {entry.tag} that was already read')
            result[entry.tag] = entry
    return result


def unpack_lenferd(f: Path) -> Iterable[BundledTranslationEntry]:
    filename = f.name
    if 'loc_' in filename:
        logger.info(f'unpack: treating {f} as loc_packages_assets_')
        bundle = 'loc_packages_assets_'
    elif 'dialogue' in filename:
        logger.info(f'unpack: treating {f} as dialogue_packages_assets_all')
        bundle = 'dialogue_packages_assets_all'

    it = iter(read_csv_lines(f))
    # first 2 lines are statistics, 3 is header
    row = next(it)
    logger.debug(f'unpack: lenferd: skip first line, {row}')
    row = next(it)
    logger.debug(f'unpack: lenferd: skip second line, {row}')
    row = next(it)
    logger.debug(f'unpack: lenferd: check header, {row}')

    headers = ['', 'code', 'entry', '', 'en', 'translation', 'uk',
               '', '', 'ru', '']
    _validate_headers(row, headers, f)
    for row in it:
        try:
            order, scene, tag, combined, en, translation, uk, machine, de, ru, check = row
        except ValueError as err:
            raise RuntimeError(f'invalid row: {row}') from err
        entry = BundledTranslationEntry(
            bundle=bundle,
            tag=tag,
            en=en,
            ru_native=ru,
            ru_machine=machine,
            ru_final=translation,
            # TODO: define format for check column?
            verified=False,
            uk=uk,
        )
        if 'DO NOT DELETE' in en:
            # verify choice stubs automatically
            entry.ru_final = en
            entry.verified = True
        yield entry


def unpack_bundle(f: Path) -> Iterable[BundledTranslationEntry]:
    it = iter(read_csv_lines(f))
    # first line is header
    row = next(it)
    logger.debug(f'unpack: bundle: check header, {row}')

    headers = ['tag', 'bundle', 'en', 'ru', 'uk']
    _validate_headers(row, headers, f)

    for row in it:
        tag, bundle, en, ru, uk, = row
        entry = BundledTranslationEntry(
            bundle=bundle,
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
            entry.ru_final = en
            entry.verified = True
        yield entry


def read_csv_lines(filepath: Path) -> Iterable[List[str]]:
    logger.info(f'opening {filepath}')
    if not filepath.is_file():
        raise RuntimeError(f'{filepath} is not a file')

    with filepath.open(encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')

        for line in reader:
            yield line


def _validate_headers(row: List[str], headers: List[str], f: Path) -> None:
    if len(row) != len(headers):
        logger.critical(f'unpack: {f} - expected {len(headers)} columns, but got {len(row)}')
        raise RuntimeError('invalid csv headers')
    row = list(h.lower() for h in row)
    for idx, actual, expected in zip(range(0,100), row, headers):
        if expected and actual != expected:
            logger.critical(f'unpack: {f} - expected header #{idx+1} to be {expected}, but got {actual}')
            raise RuntimeError('invalid csv headers')

def apply_delta(origin: TranslationMap, delta: Dict[str, BundledTranslationEntry], force: bool) -> TranslationMap:
    logger.info('applying delta')
    result = deepcopy(origin)
    for scene in result.values():
        for e in scene.entries:
            new = delta.get(e.tag)
            ru_final = e.ru_final
            ru_native = e.ru_native
            ru_machine = e.ru_machine
            if new:
                if force or new.ru_final not in (ru_final, ru_machine, ru_native):
                    logger.debug(f'apply: {e.tag}\n-{ru_final}\n+{new}')
                    e.ru_final = new.ru_final
                    if ru_machine:
                        e.ru_machine = ''
    logger.info('applying done')
    return result


def group_entries(entries: Iterable[BundledTranslationEntry]) -> TranslationMap:
    logger.info('grouping entries into translation map')
    result: TranslationMap = dict()
    for bundled in entries:
        scene = tag_to_scene(bundled.tag)
        if scene not in result:
            result[scene] = TranslationScene(bundled.bundle, scene, [])
        trans_entry = TranslationEntry(
            tag=bundled.tag,
            en=bundled.en,
            ru_native=bundled.ru_native,
            ru_machine=bundled.ru_machine,
            ru_final=bundled.ru_final,
            verified=bundled.verified,
            uk=bundled.uk,
        )
        result[scene].entries.append(trans_entry)
    logger.info('grouping done')
    return result


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
