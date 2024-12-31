import asyncio

from base64 import b64encode
import struct
from io import BytesIO
import subprocess


def calculate_duration(
    pcm_data: bytes,
    sample_rate: int,
    bytes_per_sample: int,
) -> float:
    return len(pcm_data) / (sample_rate * bytes_per_sample)


def extract_waveform_points(
    pcm_data: bytes,
    samples_needed: int,
    samples_per_point: int,
) -> list[int]:
    pcm_stream = BytesIO(pcm_data)
    waveform_points: list[int] = []

    for i in range(samples_needed):
        max_amplitude = 0
        for _ in range(samples_per_point):
            if pcm_stream.tell() < len(pcm_data) - 1:
                sample = struct.unpack("<h", pcm_stream.read(2))[0] / 32768.0
                max_amplitude = max(max_amplitude, abs(sample))

        waveform_points.append(min(255, int(max_amplitude * 255)))

        bytes_to_skip = (i + 1) * len(pcm_data) // samples_needed - pcm_stream.tell()
        pcm_stream.seek(bytes_to_skip, 1)

    return waveform_points


async def run_ffmpeg(audio: bytes):
    process = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-f",
        "mp3",
        "-i",
        "pipe:0",
        "-ac",
        "1",
        "-ar",
        "48000",
        "-f",
        "s16le",
        "pipe:1",
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout, stderr = await process.communicate(input=audio)

    if process.returncode != 0:
        raise Exception(
            f"FFmpeg failed with exit code {process.returncode}: {stderr.decode()}"
        )

    return stdout, stderr


async def generate_waveform_from_audio(audio: bytes) -> tuple[str, float]:
    sample_rate = 48000
    bytes_per_sample = 2

    pcm_data, _stderr = await run_ffmpeg(audio)
    duration_secs = calculate_duration(pcm_data, sample_rate, bytes_per_sample)

    samples_needed = min(256, int(duration_secs * 10))
    samples_per_point = len(pcm_data) // (bytes_per_sample * samples_needed)

    waveform_points = extract_waveform_points(
        pcm_data, samples_needed, samples_per_point
    )
    waveform_base64 = b64encode(bytes(waveform_points)).decode()

    return waveform_base64, duration_secs
