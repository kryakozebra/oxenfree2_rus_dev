#!/usr/bin/env python3

import logging
import shutil

from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import UnityPy

from oxenfree import (
    TranslationMap,
    TranslationScene,
    load_translation_map_from_dir,
)
from oxenfree.bundle import detect_bundle_dir, get_text_tree


logger = logging.getLogger(__name__)
if UnityPy.__version__ != '1.9.10':
    logger.warning(f'UnityPy {UnityPy.__version__} detected, but only 1.9.10 was tested!')


@dataclass
class Args:
    debug: bool
    game_dir: Path
    output_dir: Path
    translations_dir: Path
    required_bundles: List[str]


def parse_args() -> Args:
    p = ArgumentParser()
    p.add_argument('--game-dir', required=True, type=Path,
        help='Oxenfree 2 directory, containing .exe')
    p.add_argument('--output-dir', type=Path, default='output/repack_bundle/',
        help='directory to put repacked bundle contents to')
    p.add_argument('--required-bundles', nargs='+', type=Path, default=[
        # 'dialogue_packages_assets_all', # breaks the game if repacked via UnityPy
        'loc_packages_assets_',
    ], help='.bundle files to be unpacked')
    p.add_argument('--translations-dir', required=True, type=Path,
        help='path to translation JSONs that should be put into new bundle')
    p.add_argument('--debug', action='store_true',
        help='print more logs')
    return Args(**p.parse_args().__dict__)


def main(args: Args) -> None:
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    bundles = copy_bundles(args.game_dir, args.required_bundles, args.output_dir)
    translation = get_translation_map(args.translations_dir)
    repack_bundles(bundles, translation)


def copy_bundles(game_dir: Path, required_bundles: List[str], output_dir: Path) -> Dict[str, Path]:
    logger.info('copying bundles')
    if output_dir.is_dir():
        logger.info(f'copy: directory {output_dir} exists; cleanup')
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result = dict()
    bundle_dir = detect_bundle_dir(game_dir)

    for key in required_bundles:
        bundle = (
            bundle_dir / (key + '.bundle')
        ).absolute()

        if not bundle.is_file():
            raise RuntimeError(f'Bundle does not exist: {bundle}')
        new_bundle = output_dir / bundle.name
        logger.debug(f'copy: bundle to output directory')
        if new_bundle.is_file():
            logger.debug(f'file {new_bundle} exists; remove it')
            new_bundle.unlink()
        shutil.copyfile(bundle, new_bundle)
        logger.info(f'using bundle: {new_bundle}')
        result[key] = new_bundle
    return result


def get_translation_map(translations_dir: Path) -> TranslationMap:
    logger.info('loading translation JSONs...')
    result = load_translation_map_from_dir(translations_dir)
    logger.info('loading JSONs done')
    return result


def repack_bundles(bundles: Dict[str, Path], translations: TranslationMap) -> None:
    logger.info('repacking bundles...')

    for bundle_name, bundle_file in bundles.items():
        logger.info(f'loading bundle {bundle_name}...')
        env = UnityPy.load(str(bundle_file))

        for obj in env.objects:
            tree = get_text_tree(obj)
            if not tree:
                continue

            lang = tree['_ietfTag']
            obj_name = tree['m_Name']
            if lang != 'en':
                # we replace only english texts with russian translation
                continue

            logger.debug(f'repack: text {obj_name}')
            scene_entries = tree.get('_database', dict()).get('_entries', [])
            scene, _ = obj_name.split('_Text')
            translated = translations.get(scene)
            if not translated:
                # some _Text files are present but have no localization entries in them
                if scene_entries:
                    logger.error(f'repack: no translation file for scene {scene} !')
                continue
            for e in scene_entries:
                e['_localization'] = find_translation(e['_entryName'], translated)
            obj.save_typetree(tree)

        logger.info(f'repack: saving changes in {bundle_file}...')
        with open(bundle_file, 'wb') as f:
            f.write(env.file.save())

    logger.info('repacking done')


def find_translation(tag: str, scene: TranslationScene) -> str:
    for e in scene.entries:
        if e.tag != tag:
            continue
        if e.ru_final:
            return e.ru_final
        if e.ru_machine:
            return e.ru_machine
        if e.ru_native:
            return e.ru_native
        if e.en:
            return e.en
        logger.warning(f'tag {tag} found but no valid translation present in map')
        return ''
    logger.error(f'Could not find translation entry with tag {tag}')
    raise IndexError('No translation entry')


def _main() -> None:
    main(parse_args())


if __name__ == '__main__':
    _main()
