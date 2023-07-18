from copy import copy
import json
import logging
import os

from dataclasses import dataclass, is_dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class TranslationEntry:
    tag: str
    en: str
    ru_native: str
    ru_machine: str
    ru_final: str
    verified: bool
    uk: str

@dataclass
class TranslationScene:
    bundle: str
    scene: str
    entries: List[TranslationEntry]

    @staticmethod
    def load_from_file(filename: Path) -> 'TranslationScene':
        with filename.open(encoding='utf-8') as f:
            data = json.load(f)
        ts = TranslationScene(bundle=data['bundle'], scene=data['scene'], entries=[])
        for e in data['entries']:
            ts.entries.append(TranslationEntry(**e))
        return ts

    def save_to_file(self, output_dir: Path) -> None:
        logger.debug(f'scene dump: {self.scene}')
        dump_to = output_dir / (self.scene+'.json')
        with dump_to.open('w', encoding='utf-8') as f:
            sorted_self = copy(self)
            sorted_self.entries = list(sorted(self.entries, key=lambda x: x.tag))
            json.dump(sorted_self,
                f,
                indent=4,
                cls=_SceneEncoder,
                ensure_ascii=False
            )


class _SceneEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if is_dataclass(o):
            return asdict(o)
        return super().default(o)


TranslationMap = Dict[str, TranslationScene]

def load_translation_map_from_dir(dirname: Path) -> TranslationMap:
    result: TranslationMap = dict()
    for child in dirname.iterdir():
        if not (child.is_file() and child.name.endswith('.json')):
            continue
        key, _ = os.path.splitext(child.name)
        result[key] = TranslationScene.load_from_file(child)
    return result
