# -*- coding: utf-8 -*-
import asyncio, aiogram, threading, logging, random, string, math, json, time, traceback, re, os, uuid

from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import ChatActions
from aiogram import Bot, types

from aiogram.utils.exceptions import (Unauthorized, InvalidQueryID, TelegramAPIError, UserDeactivated,
									CantDemoteChatCreator, MessageNotModified, MessageToDeleteNotFound,
									MessageTextIsEmpty, RetryAfter, CantParseEntities, MessageCantBeDeleted,
									TerminatedByOtherGetUpdates, BotBlocked)

from datetime import datetime, timedelta, timezone


from middleware import ThrottlingMiddleware
from functions import *
from keyboards import *
from config import *
from loader import *



#################################################################################################################################
logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s', level=logging.INFO)
logging.getLogger("aiogram").setLevel(logging.INFO)
logging.getLogger("asyncio").setLevel(logging.WARNING)
#################################################################################################################################
class is_reg(BoundFilter):
	async def check(self, message: types.Message):
		uid, username, first_name = get_user(message)
		return uid in admin_ids

class Project(StatesGroup):
	create = State()
	search = State()
#################################################################################################################################

# Стартовая команда - /start
@dp.message_handler(is_reg(), text_startswith='/start', state='*')
async def CommandStart_(message: types.Message, state: FSMContext):
	await state.finish()
	uid, username, first_name = get_user(message)

	await message.answer(text=f'<b>Меню управления криптом</b>', reply_markup=await kb_menu(uid))




@dp.errors_handler()
async def errors_handler(update, exception):
	# Не удалось изменить сообщение
	if isinstance(exception, MessageNotModified):
		# logging.exception(f"MessageNotModified: {exception}\nUpdate: {update}")
		return True

	# Пользователь заблокировал бота
	if isinstance(exception, BotBlocked):
		# logging.exception(f"BotBlocked: {exception}\nUpdate: {update}")
		return True

	if isinstance(exception, CantDemoteChatCreator):
		logging.exception(f"CantDemoteChatCreator: {exception}\nUpdate: {update}")
		return True

	# Не удалось удалить сообщение
	if isinstance(exception, MessageCantBeDeleted):
		#logging.exception(f"MessageCantBeDeleted: {exception}\nUpdate: {update}")
		return True

	# Сообщение для удаления не было найдено
	if isinstance(exception, MessageToDeleteNotFound):
		# logging.exception(f"MessageToDeleteNotFound: {exception}\nUpdate: {update}")
		return True

	# Сообщение пустое
	if isinstance(exception, MessageTextIsEmpty):
		# logging.exception(f"MessageTextIsEmpty: {exception}\nUpdate: {update}")
		return True

	# Пользователь удалён
	if isinstance(exception, UserDeactivated):
		# logging.exception(f"UserDeactivated: {exception}\nUpdate: {update}")
		return True

	# Бот не авторизован
	if isinstance(exception, Unauthorized):
		logging.exception(f"Unauthorized: {exception}\nUpdate: {update}")
		return True

	# Неверный Query ID
	if isinstance(exception, InvalidQueryID):
		# logging.exception(f"InvalidQueryID: {exception}\nUpdate: {update}")
		return True

	# Повторите попытку позже
	if isinstance(exception, RetryAfter):
		# logging.exception(f"RetryAfter: {exception}\nUpdate: {update}")
		return True

	# Уже имеется запущенный бот
	if isinstance(exception, TerminatedByOtherGetUpdates):
		print("You already have an active bot. Turn it off.")
		logging.exception(f"TerminatedByOtherGetUpdates: {exception}\nUpdate: {update}")
		return True

	# Ошибка в HTML/MARKDOWN разметке
	if isinstance(exception, CantParseEntities):
		logging.exception(f"CantParseEntities: {exception}\nUpdate: {update}")
		return True

	# Ошибка телеграм АПИ
	if isinstance(exception, TelegramAPIError):
		logging.exception(f"TelegramAPIError: {exception}\nUpdate: {update}")
		return True

	# Все прочие ошибки
	logging.exception(f"Exception: {exception}\nUpdate: {update}")

	try:
		try: os.makedirs('temp')
		except: pass
		f_name= f'temp/{time.time()}.txt'
		open(f_name, 'w', encoding='utf-8').write(f"{str(update)}\n\n{str(traceback.format_exc())}")
		for x in admin_ids:
			try: await bot.send_document(x, document=open(f_name, 'rb'), caption=f"<b>Exception:</b> <code>{exception}</code>", reply_markup=await kb_close())
			except: pass
		threading.Thread(target=os_delete, args=[f_name]).start()
	except: pass

	return True

##################################!!! HANDLERS - UTILS | TEMP - HANDLERS !!!############################################################
@dp.callback_query_handler(text_startswith='project', state='*')
async def handler_utils(call: types.CallbackQuery, state: FSMContext, custom_data = None):
	await state.finish()
	cd = custom_data.split(':') if custom_data else call.data.split(':')

	if cd[1] == 'menu':
		await call.message.edit_text('<b>Управление проектами</b>', reply_markup=await kb_project_menu())
	
	elif cd[1] == 'create':
		if len(cd) == 2:
			await call.message.edit_text('<b>Создание проекта</b>\n<i>Введите название</i>', reply_markup=await kb_project_create(state='name'))
			await Project.create.set()
			async with state.proxy() as data:
				data['state'] = 'name'
		else:
			await call.message.edit_text('<b>Создание проекта</b>\n<i>Отправьте .zip архив проекта</i>', reply_markup=await kb_project_create(state='archive'))
			await Project.create.set()
			async with state.proxy() as data:
				data['name'] = cd[2]
				data['state'] = 'archive'

	elif cd[1] == 'search':
		await call.message.edit_text('<b>Поиск проекта</b>\n<i>Введите ID\\uuid\\название проекта </i>', reply_markup=await kb_back('project:menu'))
		await Project.search.set()

@dp.message_handler(state=Project.search)
async def Project_search(message: types.Message, state: FSMContext):
	mt = message.text.strip()

	async with httpx.AsyncClient() as client:
		resp = (await client.post(f'{website_url}/api/project', json={'action': 'get', 'id': mt if mt.isdigit() else None, 'name': mt, 'uuid': mt})).json()
		print(resp)
		if resp['error']:
			await state.finish()
			return await message.answer(f'Ошибка при поиске проекта: <b>{resp["error_desc"]}</b>', reply_markup=await kb_back('project:menu'))
		if resp['project']:
			await state.finish()
			await message.answer(f'<b>Информация о проекте</b>\n├ ID:  <code>{resp["project"]["id"]}</code>\n├ Название:  <code>{resp["project"]["name"]}</code>\n├ Соль:  <code>{resp["project"]["salt"]}</code>\n└ UUID: <code>{resp["project"]["uuid"]}</code>\n<i>Выберите файлы для крипта</i>', reply_markup=await kb_project_manage(resp['project']))
		else:
			await call.message.edit_text('<b>Поиск проекта</b>\n<b>❌ Не удалось найти проект с задаными параметрами</b>\n<i>Введите ID\\uuid\\название проекта </i>', reply_markup=await kb_back('project:menu'))



@dp.message_handler(state=Project.create, content_types=['document', 'text'])
async def Project_create(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		if data['state'] == 'name':
			mt = message.text
			data['name'] = mt
			data['state'] = 'archive'
			await message.answer(f'<b>Создание проекта</b>\n└ Название:  <code>{mt}</code>\n<i>Отправьте .zip архив проекта</i>', reply_markup=await kb_project_create(state='archive'))
		
		elif data['state'] == 'archive':
			async with httpx.AsyncClient() as client:
				resp = (await client.post(f'{website_url}/api/project', json={'action': 'create', 'name': data['name']})).json()
				if resp['error']:
					await state.finish()
					return await message.answer(f'Ошибка при создании проекта: <b>{resp["error_desc"]}</b>', reply_markup=await kb_back('project:menu'))
				data['project'] = resp['project']

				file = await bot.get_file(message.document.file_id)

				file_resp = await client.get(f'https://api.telegram.org/file/bot{bot_token}/{file.file_path}')
				resp = (await client.post(f'{website_url}/api/encrypt', params={'action': 'upload_zip'}, files={'project_uuid': (None, data['project']['uuid']), 'project_file': file_resp.content})).json()
				if resp['error']:
					await state.finish()
					return await message.answer(f'Ошибка при загрузке файлов проекта: <b>{resp["error_desc"]}</b>', reply_markup=await kb_back('project:menu'))
				data['files_to_encrypt'] = resp['files_to_encrypt']
			data['state'] = 'choose_files'
			await message.answer(f'<b>Создание проекта</b>\n└ Название:  <code>{data["name"]}</code>\n<i>Выберите файлы для крипта</i>\n0 - без крипта\n1 - крипт\n2 - крипт + ключ', reply_markup=await kb_project_create(state='choose_files', files_to_encrypt=data['files_to_encrypt']))
@dp.callback_query_handler(state=Project.create)
async def Project_create_(call: types.CallbackQuery, state: FSMContext):
	cd = call.data.split(':')
	async with state.proxy() as data:
		if len(cd) == 2 and cd[0] == '__encrypt__' and cd[1] == '__encrypt__':
			async with httpx.AsyncClient() as client:
				resp = (await client.post(f'{website_url}/api/encrypt', params={'action': 'encrypt'}, files={'project_uuid': (None, data['project']['uuid']), 'files_to_encrypt': (None, json.dumps(data['files_to_encrypt']))})).json()
				if resp['error']:
					await state.finish()
					return await call.message.edit_text(f'Ошибка при загрузке файлов проекта: <b>{resp["error_desc"]}</b>', reply_markup=await kb_back('project:menu'))

			await call.message.edit_text(f'<b>Проект создан</b>\n├ ID:  <code>{data["project"]["id"]}</code>\n├ Название:  <code>{data["project"]["name"]}</code>\n├ Соль:  <code>{data["project"]["salt"]}</code>\n└ UUID: <code>{data["project"]["uuid"]}</code>\n<i>Выберите файлы для крипта</i>\n0 - без крипта\n1 - крипт\n2 - крипт + ключ', reply_markup=await kb_project_manage(data['project']))
			await state.finish()
			return

		data['files_to_encrypt'][cd[0]] += 1 if data['files_to_encrypt'][cd[0]] in (0, 1) else -2
		await call.message.edit_text(f'<b>Создание проекта</b>\n└ Название:  <code>{data["name"]}</code>\n<i>Выберите файлы для крипта</i>\n0 - без крипта\n1 - крипт\n2 - крипт + ключ', reply_markup=await kb_project_create(state='choose_files', files_to_encrypt=data['files_to_encrypt']))


@dp.callback_query_handler(text_startswith='utils', state='*')
async def handler_utils(call: types.CallbackQuery, state: FSMContext, custom_data = None):
	cd = custom_data.split(':') if custom_data else call.data.split(':')

	if cd[1] == 'menu':
		await call.message.edit_text(text=f'<b>Меню управления криптом</b>', reply_markup=await kb_menu(uid))

	elif cd[1] == 'delete':
		try: await call.message.delete()
		except: pass
	
#################################################################################################################################
async def on_startup(dp):
	global bot_info
	bot_info = await bot.get_me()


	async def set_default_commands(dp):
		await dp.bot.set_my_commands([types.BotCommand("start", "Запустить бота")])
	await set_default_commands(dp)

if __name__ == '__main__':
	try: executor.start_polling(dp, on_startup=on_startup)
	except Exception as error:
		raise error
		logging.critical('Неверный токен бота!')