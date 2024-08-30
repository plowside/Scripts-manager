import json

from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from cashews import cache

from functions import *
from config import *

#################################################################################################################################
async def kb_construct(keyboard = None, q = {}, row_width = 2):
	if not keyboard: keyboard = InlineKeyboardMarkup(row_width)
	if type(q) is dict:
		for x in q:
			_ = q[x].split('^')
			if _[0] == 'url': keyboard.insert(InlineKeyboardButton(x,url=_[1]))

			elif _[0] == 'cd': keyboard.insert(InlineKeyboardButton(x,callback_data=_[1]))
	else:
		for x in q: keyboard.insert(x)

	return keyboard
#################################################################################################################################
cache.setup("mem://")



async def kb_menu():
	s = {'Проекты': 'cd^project:menu', 'Ключи': 'cd^key:menu'}
	keyboard = await kb_construct(InlineKeyboardMarkup(row_width=2), s)
	return keyboard




async def kb_project_menu():
	s = {'Все проекты': 'cd^project:all', 'Создать': 'cd^project:create', 'Найти': 'cd^project:search', '': 'cd^_', '↪ Назад': 'cd^utils:menu'}
	keyboard = await kb_construct(InlineKeyboardMarkup(row_width=2), s)
	return keyboard

async def kb_project_all():
	async with httpx.AsyncClient() as client:
		resp = (await client.post(f'{website_url}/api/project', json={'action': 'get_all'})).json()
		s = {x['name']: f'cd^project:search:{x["id"]}' for x in resp['project']}
	keyboard = await kb_construct(InlineKeyboardMarkup(row_width=2), s)
	keyboard.add(InlineKeyboardButton('↪ Назад', callback_data='project:menu'))
	return keyboard

async def kb_project_manage(project):
	s = {'Скачать': f'url^{website_url}/storage/{project["uuid"]}', '': 'cd^_', 'Обновить файлы': f'cd^project:update:files:{project["id"]}', '': 'cd^__', '❌ Удалить': f'cd^project:delete:{project["id"]}', '↪ Назад': 'cd^project:all'} #'✏️ Переименовать': f'cd^project:{project["id"]}:change:name'
	keyboard = await kb_construct(InlineKeyboardMarkup(row_width=2), s)
	return keyboard

async def kb_project_create(state: str = None, files_to_encrypt: dict = {}):
	row_width = 2
	if state == 'name':
		s = {'Сгенерировать рандомный': 'cd^project:create:random', '↪ Назад':'cd^project:menu'}
		row_width = 1
	elif state == 'archive':
		s = {'↪ Назад':'cd^project:menu'}
	elif state == 'choose_files':
		s = {**{f'{x} - {files_to_encrypt[x]}': f'cd^{x}' for x in files_to_encrypt}, '💎 Закриптовать': 'cd^__encrypt__:__encrypt__'}
	else:
		s = {}
	keyboard = await kb_construct(InlineKeyboardMarkup(row_width=row_width), s)
	return keyboard

async def kb_project_update(project_id: int, state: str = None, files_to_encrypt: dict = {}):
	row_width = 2
	if state == 'archive':
		s = {'↪ Назад':f'cd^project:search:{project_id}'}
	elif state == 'choose_files':
		s = {**{f'{x} - {files_to_encrypt[x]}': f'cd^{x}' for x in files_to_encrypt}, '💎 Закриптовать': 'cd^__encrypt__:__encrypt__'}
	else:
		s = {}
	keyboard = await kb_construct(InlineKeyboardMarkup(row_width=row_width), s)
	return keyboard







async def kb_key_menu():
	s = {'Создать': 'cd^key:create', 'Найти': 'cd^key:search', '↪ Назад': 'cd^utils:menu'}
	keyboard = await kb_construct(InlineKeyboardMarkup(row_width=2), s)
	return keyboard

async def kb_key_create(state: str = None):
	row_width = 2
	if state == 'select_project':
		async with httpx.AsyncClient() as client:
			resp = (await client.post(f'{website_url}/api/project', json={'action': 'get_all'})).json()
			s = {x['name']: f'cd^key:create:{x["id"]}' for x in resp['project']}
		s['↪ Назад'] = 'cd^key:menu'
	elif state == 'enter_exp_ts':
		s = {x[0]: f'cd^{x[1]}' for x in {'1 час': 3600, '2 часа': 7200, '1 день': 86400, '2 дня': 172800, '1 неделя': 604800, '1 месяц': 2592000}.items()}
		s['↪ Назад'] = 'cd^key:menu'
		row_width = 3
	elif state == 'enter_max_conns':
		s = {x: f'cd^{x}' for x in [1,2,3,4,5,10]}
		s['↪ Назад'] = 'cd^key:menu'
		row_width = 3
	else:
		s = {}
	keyboard = await kb_construct(InlineKeyboardMarkup(row_width=row_width), s)
	return keyboard

async def kb_key_change(state: str = None):
	row_width = 2
	if state == 'enter_exp_ts':
		s = {x[0]: f'cd^{x[1]}' for x in {'1 час': 3600, '2 часа': 7200, '1 день': 86400, '2 дня': 172800, '1 неделя': 604800, '1 месяц': 2592000}.items()}
		s['↪ Назад'] = 'cd^key:menu'
		row_width = 3
	else:
		s = {}
	keyboard = await kb_construct(InlineKeyboardMarkup(row_width=row_width), s)
	return keyboard

async def kb_key_manage(key):
	s = {'✏️ Продлить': f'cd^key:change:{key["id"]}:exp_ts', '❌ Удалить': f'cd^key:delete:{key["id"]}'}
	s['↪ Назад'] = 'cd^key:menu'
	keyboard = await kb_construct(InlineKeyboardMarkup(row_width=2), s)
	return keyboard




### UTILS ###
async def kb_close():
	keyboard = await kb_construct(InlineKeyboardMarkup(), {'❌ Закрыть':'cd^utils:delete'})
	return keyboard

async def kb_back(callback_data = 'user:menu', text = '↪ Назад'):
	keyboard = InlineKeyboardMarkup()
	keyboard.add(InlineKeyboardButton(text, callback_data=callback_data))
	return keyboard