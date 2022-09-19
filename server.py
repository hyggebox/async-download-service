import asyncio
from aiohttp import web
import aiofiles
import logging
import os


DEBUG_MODE = True


async def archive(request):
    archive_hash = request.match_info['archive_hash']
    files_path = os.path.join('test_photos', archive_hash)
    if not os.path.exists(files_path):
        raise web.HTTPNotFound(text='Архив не существует или был удален')
    loading_process = await asyncio.create_subprocess_exec(
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
        while not loading_process.stdout.at_eof():
            chunk = await loading_process.stdout.read(n=500*1024)
            logging.info('Sending archive chunk ...')
            await response.write(chunk)
            if DEBUG_MODE:
                await asyncio.sleep(3)

    except asyncio.CancelledError:
        logging.info('Download was interrupted')
        raise

    finally:
        loading_process.kill()
        await loading_process.communicate()
    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r', encoding='utf-8') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archive),
    ])
    web.run_app(app)
