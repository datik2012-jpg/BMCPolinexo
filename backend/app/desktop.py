"""Serve the prebuilt UI beside the existing API, without nginx."""
from pathlib import Path
import sys

from fastapi import HTTPException
from starlette.staticfiles import StaticFiles

from .main import app


def web_directory() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / 'web'
    return Path(__file__).resolve().parents[2] / 'frontend' / 'dist'


def create_app():
    directory = web_directory()
    if not (directory / 'index.html').is_file():
        raise RuntimeError('The built web interface is missing.')
    app.state.desktop_mode = True
    if not any(route.name == 'desktop-web' for route in app.routes):
        # Unknown API paths must never fall through to frontend files.
        @app.api_route('/api/{path:path}', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
        async def unknown_api(path: str):
            raise HTTPException(404)

        app.mount('/', StaticFiles(directory=directory, html=True), name='desktop-web')
    return app
