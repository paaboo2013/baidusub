#!/usr/bin/env python3
from __future__ import absolute_import, print_function, unicode_literals
from progressbar import ProgressBar, Percentage, Bar, ETA
import os
import sys
import json
import base64
import wave
import tempfile
import math
import audioop
import argparse
import subprocess
import multiprocessing
from aip import AipSpeech
from autosub.formatters import FORMATTERS

DEFAULT_SUBTITLE_FORMAT = 'srt'
DEFAULT_CONCURRENCY = 10

def getClient():
    try:
        with open('key.json', 'r') as baidukey:
            keys = json.load(baidukey)
            #print(keys['appkey'])
            return AipSpeech(keys['appid'], keys['appkey'], keys['secretkey'])
    except KeyboardInterrupt:
        print('no key file found')
        return
    

client = getClient()

# 检测是否安装某个程序

def which(program):
    def is_exe(file_path):
        return os.path.isfile(file_path) and os.access(file_path, os.X_OK)

    (fpath, fname) = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None

# 百分比？


def percentile(arr, percent):
    arr = sorted(arr)
    k = (len(arr) - 1) * percent
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return arr[int(k)]
    d0 = arr[int(f)] * (c - k)
    d1 = arr[int(c)] * (k - f)
    return d0 + d1

# 导出音频


def extract_audio(filename, channels=1, rate=16000):
    temp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    if not os.path.isfile(filename):
        print("The given file does not exist: {0}".format(filename))
        raise Exception("Invalid filepath: {0}".format(filename))
    if not which("ffmpeg"):
        print("ffmpeg: Executable not found on machine.")
        raise Exception("Dependency not found: ffmpeg")
    command = ["ffmpeg", "-y", "-i", filename, "-ac",
               str(channels), "-ar", str(rate), "-loglevel", "error", temp.name]
    use_shell = True if os.name == "nt" else False
    subprocess.check_output(command, stdin=open(os.devnull), shell=use_shell)
    return (temp.name, rate)

# 寻找声音 分割为 regions


def find_speech_regions(filename, frame_width=4096, min_region_size=0.5, max_region_size=6):
    reader = wave.open(filename)
    sample_width = reader.getsampwidth()
    rate = reader.getframerate()
    n_channels = reader.getnchannels()
    chunk_duration = float(frame_width) / rate

    n_chunks = int(math.ceil(reader.getnframes()*1.0 / frame_width))
    energies = []

    for i in range(n_chunks):
        chunk = reader.readframes(frame_width)
        energies.append(audioop.rms(chunk, sample_width * n_channels))

    threshold = percentile(energies, 0.2)

    elapsed_time = 0

    regions = []
    region_start = None

    for energy in energies:
        is_silence = energy <= threshold
        max_exceeded = region_start and elapsed_time - region_start >= max_region_size

        if (max_exceeded or is_silence) and region_start:
            if elapsed_time - region_start >= min_region_size:
                regions.append((region_start, elapsed_time))
                region_start = None

        elif (not region_start) and (not is_silence):
            region_start = elapsed_time
        elapsed_time += chunk_duration
    return regions


# 音频 转 pcm


class FLACConverter(object):
    def __init__(self, source_path, include_before=0.25, include_after=0.25):
        self.source_path = source_path
        self.include_before = include_before
        self.include_after = include_after

    def __call__(self, region):
        try:
            (start, end) = region
            start = max(0, start - self.include_before)
            end += self.include_after
            temp = tempfile.NamedTemporaryFile(suffix='.pcm')
            command = ["ffmpeg", "-ss", str(start), "-t", str(end - start),
                       "-y", "-i", self.source_path,
                       "-acodec", "pcm_s16le", "-f", "s16le", "-ac", "1", "-ar", "16000",
                       "-loglevel", "error", temp.name]
            use_shell = True if os.name == "nt" else False
            subprocess.check_output(command, stdin=open(os.devnull), shell=use_shell)
            return temp.read()

        except KeyboardInterrupt:
            return

# 识别文字


class SpeechRecognizer(object):
    def __init__(self, rate=16000, retries=3):
        self.rate = rate
        self.retries = retries
        

    def __call__(self, data):
        try:
           # 识别本地文件
            #print(self.client)
            texts = client.asr(data, 'pcm', 16000, {
                'dev_pid': 1536,
            })
            #print(texts['err_no'])
            #line = json.loads(texts)
            
            if str(texts['err_no']) == "0":
                #print(texts['result'][0])
                return texts['result'][0]
            
        except KeyboardInterrupt:
            return

# 生成字幕主函数


def generate_subtitles(
    source_path,
    output=None,
    subtitle_file_format=DEFAULT_SUBTITLE_FORMAT, 
    concurrency=DEFAULT_CONCURRENCY,):

    (audio_filename, audio_rate) = extract_audio(source_path)
    converter = FLACConverter(source_path=audio_filename)

    recognizer = SpeechRecognizer()
    regions = find_speech_regions(audio_filename)
    pool = multiprocessing.Pool(concurrency)
    transcripts = []

    if regions:
        try:
            widgets = ["Converting speech regions to pcm files: ", Percentage(), ' ', Bar(), ' ', ETA()]
            pbar = ProgressBar(widgets=widgets, maxval=len(regions)).start()
            extracted_regions = []
            for i, extracted_region in enumerate(pool.imap(converter, regions)):
                extracted_regions.append(extracted_region)
                pbar.update(i)
            pbar.finish()

            widgets = ["Performing speech recognition: ", Percentage(), ' ', Bar(), ' ', ETA()]
            pbar = ProgressBar(widgets=widgets, maxval=len(regions)).start()

            for i, transcript in enumerate(pool.imap(recognizer, extracted_regions)):
                transcripts.append(transcript)
                pbar.update(i)
            pbar.finish()

        except KeyboardInterrupt:
            pbar.finish()
            pool.terminate()
            pool.join()
            print("Cancelling transcription")
            raise

    timed_subtitles = [(r, t) for r, t in zip(regions, transcripts) if t]
    formatter = FORMATTERS.get(subtitle_file_format)
    formatted_subtitles = formatter(timed_subtitles)

    dest = output

    if not dest:
        (base, ext) = os.path.splitext(source_path)
        dest = "{base}.{format}".format(base=base, format=subtitle_file_format)

    with open(dest, 'wb') as f:
        f.write(formatted_subtitles.encode("utf-8"))

    os.remove(audio_filename)

    return dest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source_path', help="Path to the video or audio file to subtitle.", nargs='?')
    parser.add_argument('-f', '--format', help="Destination subtitle fromat. support srt vtt json raw.", default=DEFAULT_SUBTITLE_FORMAT)
    parser.add_argument('-o', '--output',
                        help="Output path for subtitles (by default, subtitles are saved in \
                        the same directory and name as the source path).")
    parser.add_argument('-c', '--concurrency', help="Number of concurrent API requests to make.",
                        type=int, default=DEFAULT_CONCURRENCY)
    args = parser.parse_args()

    if not args.source_path:
        return
    try:
        subtitle_file_path = generate_subtitles(
            args.source_path,
            output=args.output,
            subtitle_file_format=args.format, 
            concurrency=args.concurrency,)
        print("Subtitles file created at {}".format(subtitle_file_path))
    except KeyboardInterrupt:
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
