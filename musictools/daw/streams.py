import abc
import io
import itertools
import pickle
import random
import time

import errno
from threading import Thread

import collections
import numpy as np
import os
import pyaudio
from scipy.io import wavfile
# import matplotlib.pyplot as plt
import subprocess
import numpy as np
from musictools import config
from pathlib import Path

from .. import config


def float32_to_int16(signal: np.ndarray, dtype='int16'):
    """Convert floating point signal with a range from -1 to 1 to PCM.
    Any signal values outside the interval [-1.0, 1.0) are clipped.
    No dithering is used.
    Note that there are different possibilities for scaling floating
    point numbers to PCM numbers, this function implements just one of
    them.  For an overview of alternatives see
    http://blog.bjornroche.com/2009/12/int-float-int-its-jungle-out-there.html
    """
    if signal.dtype.kind != 'f':
        raise TypeError("'signal' must be a float array")
    dtype = np.dtype(dtype)
    if dtype.kind not in 'iu':
        raise TypeError("'dtype' must be an integer type")

    i = np.iinfo(dtype)
    abs_max = 2 ** (i.bits - 1)
    offset = i.min + abs_max
    return (signal * abs_max + offset).clip(i.min, i.max).astype(dtype)


class Stream(abc.ABC):
    @abc.abstractmethod
    def write(self, data: np.ndarray):
        """data.dtype must be float32"""
        ...


class Bytes(Stream):
    def __enter__(self):
        return io.BytesIO()


class WavFile(Stream):
    def __init__(self, path, dtype='int16'):
        if dtype not in {'float32', 'int16'}:
            raise ValueError('unsupported wave format')
        self.path = path
        self.dtype = dtype

    def __enter__(self):
        # kinda workarounds, maybe there are a better ways
        # self.arrays = []
        self.stream = io.BytesIO()
        return self

    def write(self, data: np.ndarray):
        # self.arrays.append(data)
        self.stream.write(data.tobytes())

    def __exit__(self, type, value, traceback):
        # data = np.concatenate(self.arrays) # TODO: not works, fix it
        # assert data.dtype == 'float32'
        data = np.frombuffer(self.stream.getvalue(), dtype='float32')
        if self.dtype == 'int16':
            data = float32_to_int16(data)
        wavfile.write(self.path, config.sample_rate, data)


class PCM16File(Stream):
    """
    pcm_s16le PCM signed 16-bit little-endian
    """
    def __init__(self, path):
        self.path = open(path, 'wb')

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.path.close()

    def write(self, data: np.ndarray):
        self.path.write(float32_to_int16(data).tobytes())
        # float32_to_int16(data).tofile(self.path)


class Speakers(Stream):
    def __enter__(self):
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(format=pyaudio.paFloat32, channels=1, rate=config.sample_rate, output=True)
        return self
        # return self.stream

    def __exit__(self, type, value, traceback):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

    def write(self, data: np.ndarray):
        self.stream.write(data.tobytes())

# https://support.google.com/youtube/answer/6375112
frame_width = 426
frame_height = 240

# fig, ax = plt.subplots(figsize=(frame_width / 100, frame_height / 100), frameon=False, dpi=100)
#
# R = np.random.randint(-200, 0, size=(frame_height, frame_width))
# im = plt.imshow(R)
# ax.grid(False)
# ax.axis('off')
# images = []
# for _ in range(16):
#     b = io.BytesIO()
#     R = np.random.randint(-200, 0, size=(frame_height, frame_width))
#     im.set_data(R)
#     fig.savefig(b, format='rgba', dpi=100)
#     images.append(b)



# audio_seconds_written = 0.

audio_data = collections.deque()
video_data = collections.deque()
audio_finished = False
video_finished = False
no_more_data = False
audio_seconds_written = 0.
video_seconds_written = 0.


class GenerateAudioToPipe(Thread):
    def __init__(self):
        super().__init__()
        self._pipe_name = config.audio_pipe


    def run(self):
        global audio_finished
        global audio_seconds_written
        fd = open(self._pipe_name, 'wb')
        print('GenerateAudioToPipe')

        while not no_more_data or len(audio_data) > 0:
            print('1111111111111GenerateAudioToPipe')

            if not audio_data:
                print('***********AUDIO', len(audio_data))
                time.sleep(1)
                continue

            while audio_data:
                print('44444444444 AUDIO')
                b = audio_data.pop()
                # print(b, b.tobytes()[:100])
                fd.write(b.tobytes())
                print('5555555555')
                audio_seconds_written += len(b) / config.sample_rate


        fd.close()
        print('IIIIIIIIIII')
        audio_finished = True



class GenerateVideoToPipe(Thread):
    def __init__(self):
        super().__init__()
        self._pipe_name = config.video_pipe
        with open('/Users/tandav/GoogleDrive/projects/yt-stream/images.pkl', 'rb') as f:
            self.images = pickle.load(f)

    def run(self):
        # global video_seconds_written
        fd = open(self._pipe_name, 'wb')
        frames_written = 0
        video_seconds_written = 0

        seconds_to_write = 0.

        while True:
            if audio_finished:
                if frames_written == int(audio_seconds_written * config.fps):
                    print('gg', audio_seconds_written)
                    break

            if frames_written == 0:
                seconds_to_write = 1
            else:
                seconds_to_write = audio_seconds_written - video_seconds_written

            n_frames = int(config.fps * seconds_to_write)
            print('n_frames, seconds_to_write', n_frames, audio_seconds_written, video_seconds_written, seconds_to_write)
            if n_frames == 0:
                time.sleep(1)

            for frame in range(n_frames):
                b = random.choice(self.images).getvalue()
                fd.write(b)
                frames_written += 1
            video_seconds_written += seconds_to_write
        fd.close()


def recreate(p):
    p = Path(p)
    if p.exists():
        p.unlink()
    os.mkfifo(p)


class YouTube(Stream):
    def __init__(self, path):

        recreate(config.audio_pipe)
        recreate(config.video_pipe)

        # INPUT_AUDIO = config.audio_pipe
        OUTPUT_VIDEO = str(Path.home() / 'Desktop/radiant2.mp4')

        cmd = ('ffmpeg',
           '-loglevel', 'trace',
           '-hwaccel', 'videotoolbox',
           # '-threads', '16',
           # '-y', '-r', '60', # overwrite, 60fps
           '-y', '-r', str(config.fps),  # overwrite, 60fps
           '-s', f'{frame_width}x{frame_height}',  # size of image string
           '-f', 'rawvideo',
           '-pix_fmt', 'rgba',  # format
           # '-f', 'image2pipe',
           # '-i', 'pipe:', '-', # tell ffmpeg to expect raw video from the pipe
           # '-i', '-',  # tell ffmpeg to expect raw video from the pipe
           # '-i', f'pipe:{config.video_pipe}',  # tell ffmpeg to expect raw video from the pipe
           '-thread_queue_size', '512',
           '-i', config.video_pipe,  # tell ffmpeg to expect raw video from the pipe

           "-f", 's16le',  # means 16bit input
           "-acodec", "pcm_s16le",  # means raw 16bit input
           '-r', "44100",  # the input will have 44100 Hz
           '-ac', '1',  # number of audio channels (mono1/stereo=2)
           # '-i', f'pipe:{config.audio_pipe}',
           '-thread_queue_size', '512',
           '-i', config.audio_pipe,
           # '-b:a', "3000k",  # output bitrate (=quality). Here, 3000kb/second

           '-deinterlace',
           # '-c:v', 'hevc_videotoolbox',
           '-c:v', 'libx264',
           '-pix_fmt', 'yuv420p',
           # '-tag:v', 'hvc1', '-profile:v', 'main10',
           # '-b:v', '16M',
           # '-b:v', '1M',
           # '-b:v', '100k',

           # '-f', 'flv',
           # '-flvflags', 'no_duration_filesize',
           # 'rtmp://a.rtmp.youtube.com/live2/u0x7-vxkq-6ym4-s4qk-0acg',

           OUTPUT_VIDEO,  # output encoding
        )



        # self.ffmpeg = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        self.ffmpeg = subprocess.Popen(cmd)
        # self.p = None
        # time.sleep(5)
        # print(self.p)
        # print('2'* 100)

        self.audio_thread = GenerateAudioToPipe()
        self.video_thread = GenerateVideoToPipe()
        self.audio_thread.start()
        self.video_thread.start()

        # self.video = os.open(config.video_pipe, os.O_WRONLY | os.O_NONBLOCK)
        # self.audio = os.open(config.audio_pipe, os.O_WRONLY | os.O_NONBLOCK)

        # try:
        #     self.video = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
        # except OSError as e:
        #     if e == errno.ENOENT:
        #         print(e)
        #         self.video = None
        #
        #
        # try:
        #     self.audio = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
        # except OSError as e:
        #     if e == errno.ENOENT:
        #         print(e)
        #         self.audio = None
        #
        #
        #
        # self.video = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
        print('1'* 100)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        global audio_finished, video_finished, no_more_data
        audio_finished = True
        video_finished = True
        no_more_data = True

        self.audio_thread.join()
        self.video_thread.join()
        self.ffmpeg.wait()

        # os.close(self.audio)
        # os.close(self.video)
        # self.path.close()

    def write(self, data: np.ndarray):
        # global audio_seconds_written
        # audio_written, video_written = False, False

        # write audio samples
        # self.path.write(float32_to_int16(data).tobytes())
        a = float32_to_int16(data)#.tobytes()
        # ab = os.write(self.audio, a)
        seconds = len(data) / config.sample_rate

        audio_data.appendleft(a)

        # n_frames = int(config.fps * seconds)
        #
        # for frame in range(n_frames):
        #     v = random.choice(images).getvalue()
        #     video_data.appendleft(v)
        #
        # print('written --------', seconds, n_frames, len(audio_data), len(video_data))


        # v = b''.join(random.choice(self.images).getvalue() for frame in range(n_frames))
        # V = set(random.choice(self.images).getvalue() for frame in range(n_frames))
        # V_done = set()
        # print(len(a), len(v))
        # print(len(a), sum(len(v) for v in V), len(V))
        # retry_times = itertools.cycle((1, 1, 1, 1, 1, 1, 2, 3, 5))
        #
        #
        # t = time.time()
        #
        # while not (audio_written and video_written):
        #     if not audio_written:
        #         try:
        #             ab = os.write(self.audio, a)
        #         except BlockingIOError:
        #             print('AUDIO fails', t)
        #         else:
        #             print('AUDIO write sucess', t, ab)
        #             audio_written = True
        #
        #     if not video_written:
        #         try:
        #             for v in V - V_done:
        #                 os.write(self.video, v)
        #         except BlockingIOError:
        #             print('VIDEO fails', t, len(V))
        #         else:
        #             print('VIDEO write sucess', t)
        #             video_written = True
        #     r = next(retry_times)
        #     time.sleep(r)

        # while True:
        #     try:
        #         os.write(self.audio, b)
        #
        #     except BlockingIOError:
        #         r = next(retry_times)
        #         print('AUDIO retry', len(b), time.time(), r)
        #         time.sleep(next(retry_times))
        #     else:
        #         print('AUDIO write sucess', time.time())
        #         break

        # write video frames
        # for frame in range(n_frames):
        #     # self.p.stdin.write(random.choice(self.images).getvalue())
        #     b = random.choice(self.images).getvalue()
        #
        #     retry_times = itertools.cycle((1, 1, 1, 1, 1, 1, 2, 3, 5))
        #
        #     while True:
        #         try:
        #             os.write(self.video, b)
        #         except BlockingIOError:
        #             r = next(retry_times)
        #             print('VIDEO retry', len(b), time.time(), r)
        #             time.sleep(next(retry_times))
        #         else:
        #             print('VIDEO write sucess', time.time())
        #             break
        # self.p.communicate()
