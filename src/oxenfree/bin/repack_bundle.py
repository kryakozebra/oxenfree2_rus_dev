#!/usr/bin/env python3

import logging
import shutil

from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
from subprocess import check_call
from typing import Dict, List

from oxenfree.bundle import detect_bundle_dir


logger = logging.getLogger(__name__)


@dataclass
class Args:
    debug: bool
    game_dir: Path
    output_dir: Path
    translations_dir: Path
    required_bundles: List[str]
    repack_tool: Path


def parse_args() -> Args:
    p = ArgumentParser()
    p.add_argument('--game-dir', required=True, type=Path,
        help='Oxenfree 2 directory, containing .exe')
    p.add_argument('--output-dir', type=Path, default='output/repack_bundle/',
        help='directory to put repacked bundle contents to')
    p.add_argument('--required-bundles', nargs='+', type=Path, default=[
        'dialogue_packages_assets_all',
        'loc_packages_assets_',
    ], help='.bundle files to be unpacked')
    p.add_argument('--translations-dir', required=True, type=Path,
        help='path to translation JSONs that should be put into new bundle')
    p.add_argument('--repack_tool', type=Path, default='./textrepack.exe',
        help='path to the executable that will be used to patch .bundle files')
    p.add_argument('--debug', action='store_true',
        help='print more logs')
    return Args(**p.parse_args().__dict__)


def main(args: Args) -> None:
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    bundles = copy_bundles(args.game_dir, args.required_bundles, args.output_dir)
    repack_bundles(bundles, args.translations_dir, args.repack_tool)


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


def repack_bundles(
        bundles: Dict[str, Path],
        translation_dir: Path,
        tool: Path,
    ) -> None:
    logger.info('repacking bundles...')

    for bundle_name, bundle_file in bundles.items():
        logger.info(f'patching bundle {bundle_name}...')
        cmd = [str(tool.absolute()), str(bundle_file.absolute()), str(translation_dir.absolute())]
        logger.debug(f'>>> {cmd}')
        check_call(cmd)

    for _, bundle_file in bundles.items():
        bundle_mod = Path(str(bundle_file) + '.mod')
        logger.info(f'{bundle_mod} -> {bundle_file.name}')
        bundle_file.unlink()
        bundle_mod.rename(bundle_file)


    logger.info('repacking done')


def _main() -> None:
    main(parse_args())


if __name__ == '__main__':
    _main()
