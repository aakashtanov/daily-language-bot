import os
import subprocess
import tempfile
import logging

from gtts import gTTS


logger = logging.getLogger(__name__)


def get_duration(path: str) -> int:
    res = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', path],
        capture_output=True,
        text=True
    )
    return int(float(res.stdout.strip()))


def generate_voice_track(words: list[str], audio_dir: str, out_name: str, lang: str) -> str:
    out_path = os.path.join(audio_dir, out_name)
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

    mp3_path = ''
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
        mp3_path = tmp.name
        tts = gTTS(text='. '.join(words), lang=lang.lower(), slow=True)
        tts.save(mp3_path)

    # 5) Convert MP3 → Telegram voice (OGG / Opus)
    voice_ogg = os.path.join(audio_dir, out_path)
    logger.info(f'Converting to voice track into {voice_ogg}')
    subprocess.run([
            'ffmpeg',
            '-y',
            # '-i', concatenated_mp3,
            '-i', mp3_path,
            '-c:a', 'libopus',
            '-ac', '1',
            '-ar', '24000',
            '-application', 'voip',
            voice_ogg,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return voice_ogg
