import logging
from pathlib import Path

from typing import Any, Dict, Optional

from UnityPy.files import ObjectReader

logger = logging.getLogger(__name__)


def get_text_tree(obj: ObjectReader) -> Optional[Dict[str, Any]]:
    if obj.type.name != 'MonoBehaviour':
        return None
    if not obj.serialized_type.nodes:
        logger.warning(f'bundle: {obj} does not have any nodes!')
        return None
    try:
        tree = obj.read_typetree()
    except (ValueError, SystemError) as e:
        logger.warning(f'bundle: failed to read typetree; some object skipped:\n{e}')
        return None
    obj_name = tree['m_Name']
    # if not '_Text' in obj_name:
    if not obj_name.endswith(('_Text', '_Text_uk', '_Text_en', '_Text_ru')):
        return None
    return tree


def detect_bundle_dir(game_dir: Path) -> Path:
    if (game_dir / 'Oxenfree2_Data').is_dir() and (game_dir / 'Oxenfree2.exe').is_file():
        logger.debug('we are in game root')
        game_dir = game_dir / 'Oxenfree2_Data' / 'StreamingAssets' / 'aa' / 'StandaloneWindows64'
    else:
        logger.debug('assume we are in asset folder already')

    if (game_dir / 'loc_packages_assets_.bundle').is_file():
        return game_dir
    
    b = game_dir / 'loc_packages_assets_.bundle'
    logger.error(f'bundles: file {b} not found! Invalid folder')
    raise RuntimeError('Invalid game_dir folder')
