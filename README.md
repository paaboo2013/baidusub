

# Baidusub  [Baidusub at pypi](https://pypi.python.org/pypi/baidusub "Baidusub") 
### Auto-generated subtitles for any video

Baidusub is forked from autosub from https://github.com/agermanidis/autosub. thanks for that. Baidusub is a utility for automatic speech recognition and subtitle generation. It takes a video or an audio file as input, performs voice activity detection to find speech regions, makes parallel requests to Baidu Web Speech API to generate transcriptions for those regions (will not translates them to a different language for now) , and finally saves the resulting subtitles to disk. It can currently produce subtitles in either the SRT format or simple JSON.

### note
It only identify chinese now.

### Installation

1. Install [ffmpeg](https://www.ffmpeg.org/).
2. Run `pip install baidusub`.

### Usage
1. register a baidu asr app at [baidu ai](http://ai.baidu.com/tech/speech/asr)
2. put key.json file below to the video folder.
```
{
  "appid":"your app id",
  "appkey":"your app key",
  "secretkey":"your app secret key"
}
```
3. command
```
$ baidusub -h
usage: baidusub [-h] [-C CONCURRENCY] [-o OUTPUT] [-F FORMAT] [--list-formats] [source_path]

positional arguments:
  source_path           Path to the video or audio file to subtitle

optional arguments:
  -h, --help            show this help message and exit
  -C CONCURRENCY, --concurrency CONCURRENCY
                        Number of concurrent API requests to make
  -o OUTPUT, --output OUTPUT
                        Output path for subtitles (by default, subtitles are
                        saved in the same directory and name as the source
                        path)
  -F FORMAT, --format FORMAT
                        Destination subtitle format
  --list-formats        List all available subtitle formats
```

### License

MIT
