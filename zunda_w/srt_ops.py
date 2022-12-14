import datetime
from dataclasses import dataclass
from functools import cached_property
from itertools import chain
from pathlib import Path
from typing import Sequence, List, Callable

import srt
from pydub import AudioSegment
from srt import Subtitle

from zunda_w.voice_vox import read_output_waves
from zunda_w.words import WordFilter


@dataclass
class SpeakerUnit:
    subtitle: Subtitle
    audio: AudioSegment


@dataclass
class SpeakerCompose:
    unit: List[SpeakerUnit]
    # whisper計測の会話総時間
    n_length: datetime.timedelta

    @cached_property
    def audio_duration(self) -> datetime.timedelta:
        """
        unit.audioの総時間
        :return:
        """
        return datetime.timedelta(milliseconds=sum(map(lambda x: len(x.audio), self.unit)))


def _parse_with_id(srt_file_path: str, id: int, encoding: str, wave_path: str) -> List[SpeakerUnit]:
    subtitles = list(srt.parse(Path(srt_file_path).read_text(encoding=encoding)))
    for s in subtitles:
        s.speaker = id

    audio = list(read_output_waves(wave_path))
    return [SpeakerUnit(s, a) for s, a in zip(subtitles, audio)]


def merge(srt_files: Sequence[str], tts_dirs: Sequence[str], encoding='UTF-8',
          word_filter: WordFilter = None) -> SpeakerCompose:
    """
    SubtitleとAudiosを読み込み，時間順にソートする
    """
    units: List[SpeakerUnit] = list(chain.from_iterable(
        map(lambda x: _parse_with_id(x[1][0], x[0], encoding, x[1][1]), enumerate(zip(srt_files, tts_dirs)))))
    units.sort(key=lambda s: s.subtitle.start)
    if word_filter:
        units = list(filter(lambda unit: word_filter.is_exclude(unit.subtitle.content), units))
    time_length = units[-1].subtitle.end
    return SpeakerCompose(units, time_length)
