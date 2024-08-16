import asyncio, httpx, time

from typing import Annotated, Union

from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Cookie, Request, Response
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from .api.routers import router as api_router
from .database.database import db

#################################################################################################################################
async def process_tasks_on_startup():
	await db.init_pool()



#################################################################################################################################
@asynccontextmanager
async def lifespan(app: FastAPI):
	await process_tasks_on_startup()
	yield
	await db.close_pool()

app = FastAPI(lifespan=lifespan, title='Scheduler', docs_url=None, redoc_url=None)
app.mount('/storage', StaticFiles(directory='app/storage'), name='storage')
app.include_router(api_router)
app.add_middleware(
	CORSMiddleware,
	allow_origins=['*'],
	allow_credentials=True,
	allow_methods=['*'],
	allow_headers=['*'],
)
#################################################################################################################################

@app.get('/ts')
async def ts(request: Request):
	return time.time()

@app.get('/headers')
async def headers(request: Request):
	return request.headers