import argparse
import asyncio
from aiohttp import web
import aiofiles
import logging
import os


async def archive(request):
    archive_hash = request.match_info['archive_hash']
    files_path = os.path.join(photos_dir_path, archive_hash)
    if not os.path.exists(files_path):
        raise web.HTTPNotFound(text='Архив не существует или был удален')
    process = await asyncio.create_subprocess_exec(
        'zip', '-r', '-', '.',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=files_path
    )

    response = web.StreamResponse()
    response.headers['Content-Type'] = 'text/html'
    response.headers['Content-Disposition'] = 'attachment; filename="photos.zip"'

    await response.prepare(request)

    try:
        while not process.stdout.at_eof():
            chunk = await process.stdout.read(n=500*1024)
            logging.info('Sending archive chunk ...')
            await response.write(chunk)
            if args.delay:
                await asyncio.sleep(args.delay)

    except asyncio.CancelledError:
        logging.info('Download was interrupted')
        raise

    finally:
        process.kill()
        await process.communicate()
    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r', encoding='utf-8') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--logging', '-l',
        action='store_true',
        help='Turns on logging'
    )
    parser.add_argument(
        '--delay', '-d',
        type=int,
        help='Turns on response delay in seconds specified'
    )
    args = parser.parse_args()

    photos_dir_path = os.getenv('PHOTOS_DIR', default='test_photos')

    if args.logging:
        logging.basicConfig(level=logging.INFO)

    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archive),
    ])
    web.run_app(app)
