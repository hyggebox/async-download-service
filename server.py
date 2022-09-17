import asyncio
from aiohttp import web
import aiofiles
import os


async def archive(request):
    archive_hash = request.match_info['archive_hash']
    dir_name = os.path.join('test_photos', archive_hash)
    archive = await asyncio.create_subprocess_exec(
        'zip', '-r', '-', dir_name,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=dir_name
    )

    response = web.StreamResponse()
    response.headers['Content-Type'] = 'text/html'
    response.headers['Content-Disposition'] = 'attachment; filename="photos.zip"'

    await response.prepare(request)

    while not archive.stdout.at_eof():
        archive_piece = await archive.stdout.read(n=500*1024)
        await response.write(archive_piece)

    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r', encoding='utf-8') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archive),
    ])
    web.run_app(app)
