import logging
import asyncio
from config import TEMP_DIR, OTHER_CONSTANTS
from yt_dlp import YoutubeDL

# Configure logging
logging.basicConfig(level=logging.INFO)

async def download_video(url):
    try:
        loop = asyncio.get_running_loop()
        ydl_opts = {
            'format': 'best',
            'outtmpl': f'{TEMP_DIR}/%(title)s.%(ext)s',
        }

        with YoutubeDL(ydl_opts) as ydl:
            # Use run_in_executor for blocking operations
            await loop.run_in_executor(None, ydl.download, [url])
        logging.info(f'Successfully downloaded video: {url}')
    except Exception as e:
        logging.error(f'Error downloading video {url}: {e}')

async def main(urls):
    tasks = [download_video(url) for url in urls]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    video_urls = ['http://example.com/video1', 'http://example.com/video2']
    asyncio.run(main(video_urls))