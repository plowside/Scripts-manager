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



async def kb_menu(uid):
	s = {'Проекты': 'cd^project:menu', 'Ключи': 'cd^license_key:menu'}
	keyboard = await kb_construct(InlineKeyboardMarkup(row_width=2), s)
	return keyboard


async def kb_project_menu():
	s = {'Создать': 'cd^project:create', 'Найти': 'cd^project:search', '↪ Назад': 'cd^utils:menu'}
	keyboard = await kb_construct(InlineKeyboardMarkup(row_width=2), s)
	return keyboard

async def kb_project_manage(project):
	s = {'✏️ Переименовать': f'cd^project:{project["id"]}:change:name', 'Удалить': f'cd^project:{project["id"]}:delete', '↪ Назад': 'cd^utils:menu'}
	keyboard = await kb_construct(InlineKeyboardMarkup(row_width=2), s)
	return keyboard

async def kb_project_create(state: str = None, files_to_encrypt: dict = {}):
	print(state)
	if state == 'name':
		s = {'Сгенерировать рандомный': 'cd^project:create:random', '↪ Назад':'cd^project:menu'}
	elif state == 'archive':
		s = {'↪ Назад':'cd^project:menu'}
	elif state == 'choose_files':
		s = {**{f'{x} - {files_to_encrypt[x]}': f'cd^{x}' for x in files_to_encrypt}, '💎 Закриптовать': 'cd^__encrypt__:__encrypt__'}
	else:
		s = {}
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