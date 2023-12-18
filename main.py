import argparse
import io
import subprocess
import os
from pytube import YouTube, Playlist
from pytube.cli import on_progress
from pytube.exceptions import VideoUnavailable, PytubeError

AUDIO_DOWNLOAD_DIR = "./downloads/audios"
VIDEO_DOWNLOAD_DIR = "./downloads/videos"

def on_compelete_video_download(stream, file_path):
    print(f"Video downloaded on {file_path}")

def on_complete_audio_download(stream, file_path):
    print(f"Audio download")

def YoutubeAudioDownload(video_url, output_path = AUDIO_DOWNLOAD_DIR):
    video = YouTube(video_url,
                    on_progress_callback=on_progress,
                    on_complete_callback=on_complete_audio_download)
    
    metadata = dict(title=video.title,
                    author=video.author,
                    length=video.length,
                    publish_date=video.publish_date,
                    author_url=video.channel_url,
                    rating=video.rating,
                    )
    audio = video.streams.filter(only_audio=True).order_by('abr').desc().first()

    try:
        # filename = f"{audio.title}.mp3"
        # stream, file_path = audio.download(output_path, filename=filename)
        # print(audio)
        # print(f"audio was downloaded for {audio.title}")

        # Get the video stream as byte
        audio_data = io.BytesIO()
        audio.stream_to_buffer(audio_data)

        convertVideoToAudio(audio_data.getvalue(),
                            output_path,
                            metadata
                            )
        
    except (VideoUnavailable, PytubeError) as e:
        print(f"Error: {e}")
        print(f"Failed to download audio for {audio.title}")
    

def YoutubeVideoDownload(video_url, output_path = VIDEO_DOWNLOAD_DIR):
        
    video = YouTube(video_url,
                    on_progress_callback=on_progress,
                    on_complete_callback=on_compelete_video_download)
    
    video = video.streams.filter(only_audio=False, progressive=True).get_highest_resolution()

    try:
        video.download(output_path, filename_prefix=f'[{video.resolution}]_')
        # print(video)
        
    except (VideoUnavailable, PytubeError) as e:
        print(f"Error: {e}")
        print(f"Unable to download video {video.title}!")

def PlaylistAudioDownload(playlist_url):
    playlist = Playlist(playlist_url)
    output_path = f"{AUDIO_DOWNLOAD_DIR}/{playlist.title}"

    for video_url in playlist.video_urls:
        YoutubeAudioDownload(video_url, output_path)

def PlaylistVideoDownload(playlist_url):
    playlist = Playlist(playlist_url)
    output_path = f"{VIDEO_DOWNLOAD_DIR}/{playlist.title}"

    for video_url in playlist.video_urls:
        YoutubeVideoDownload(video_url, output_path)

def convertVideoToAudio(input_stream, output_path, metadata, bitrate='256k'):
    try:
        print("processing...")
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        output_file = f"{output_path}/{metadata['title']}.mp3"

        command = [
            'ffmpeg',
            '-i', '-',
            '-metadata', f'title={metadata["title"]}',
            '-metadata', f'publisher={metadata["author"]}',
            '-metadata', f'artist={metadata["author"]}',
            '-metadata', f'author_url={metadata["author_url"]}',
            '-metadata', f'length={metadata["length"]}' ,
            '-metadata', f'date={metadata["publish_date"].year}', 
            '-metadata', f'rating={metadata["rating"]}', 
            '-b:a', bitrate, 
            f"{output_file}"
        ]

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        stdout, stderr = process.communicate(input=input_stream)

        if process.returncode != 0:
            print(f"Return Code: {process.returncode}")
            print("Standard Output:", stdout.decode())
            print("Standard Error:", stderr.decode())

        print("[+]convert video to audio completed")
        print("file path: ", output_file)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print("Failed to convert")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--video", required=True, help="Youtube Video Url")
    ap.add_argument("-a", "--audio", required=False, help="Audio only", action=argparse.BooleanOptionalAction)
    ap.add_argument("-pl", "--playlist", required=False, help="Playlist", action=argparse.BooleanOptionalAction)
    args = vars(ap.parse_args())

    if args["playlist"] and args["audio"]:
        PlaylistAudioDownload(args["video"])
    elif args["playlist"]:
        PlaylistVideoDownload(args["video"])
    elif args["audio"]:
        YoutubeAudioDownload(args["video"])
    else:
        YoutubeVideoDownload(args["video"])

    # Usage:
    # python main.py -a -v "[Youtube video URL]"
    # python main.py -v "[Youtube video URL]"
    
