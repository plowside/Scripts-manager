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

class Key(StatesGroup):
	create = State()
	search = State()
	change = State()
#################################################################################################################################

# Стартовая команда - /start
@dp.message_handler(is_reg(), text_startswith='/start', state='*')
async def CommandStart_(message: types.Message, state: FSMContext):
	await state.finish()
	uid, username, first_name = get_user(message)

	await message.answer(text=f'<b>Меню управления криптом</b>', reply_markup=await kb_menu())




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
	
	elif cd[1] == 'all':
		await call.message.edit_text('<b>Все проекты</b>', reply_markup=await kb_project_all())

	elif cd[1] == 'delete':
		async with httpx.AsyncClient() as client:
			resp = await client.post(f'{website_url}/api/project', json={'action': 'delete', 'id': int(cd[2])})

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
		if len(cd) == 2:
			await call.message.edit_text('<b>Поиск проекта</b>\n<i>Введите ID\\uuid\\название проекта </i>', reply_markup=await kb_back('project:menu'))
			await Project.search.set()
		else:
			async with httpx.AsyncClient() as client:
				resp = (await client.post(f'{website_url}/api/project', json={'action': 'get', 'id': int(cd[2])})).json()
				if resp['error']:
					await state.finish()
					return await call.message.edit_text(f'Ошибка при поиске проекта: <b>{resp["error_desc"]}</b>', reply_markup=await kb_back('project:menu'))
				if resp['project']:
					await state.finish()
					await call.message.edit_text(f'<b>Информация о проекте</b>\n├ ID:  <code>{resp["project"]["id"]}</code>\n├ Название:  <code>{resp["project"]["name"]}</code>\n├ Соль:  <code>{resp["project"]["salt"]}</code>\n└ UUID: <code>{resp["project"]["uuid"]}</code>', reply_markup=await kb_project_manage(resp['project']))
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

			await call.message.edit_text(f'<b>Проект создан</b>\n├ ID:  <code>{data["project"]["id"]}</code>\n├ Название:  <code>{data["project"]["name"]}</code>\n├ Соль:  <code>{data["project"]["salt"]}</code>\n└ UUID: <code>{data["project"]["uuid"]}</code>', reply_markup=await kb_project_manage(data['project']))
			await state.finish()
			return

		data['files_to_encrypt'][cd[0]] += 1 if data['files_to_encrypt'][cd[0]] in (0, 1) else -2
		await call.message.edit_text(f'<b>Создание проекта</b>\n└ Название:  <code>{data["name"]}</code>\n<i>Выберите файлы для крипта</i>\n0 - без крипта\n1 - крипт\n2 - крипт + ключ', reply_markup=await kb_project_create(state='choose_files', files_to_encrypt=data['files_to_encrypt']))

@dp.message_handler(state=Project.search)
async def Project_search(message: types.Message, state: FSMContext):
	mt = message.text.strip()
	async with httpx.AsyncClient() as client:
		payload = {'action': 'get', 'name': mt, 'uuid': mt}
		if mt.isdigit(): payload['id'] = mt
		resp = (await client.post(f'{website_url}/api/project', json=payload)).json()
		if resp['error']:
			await state.finish()
			return await message.answer(f'Ошибка при поиске проекта: <b>{resp["error_desc"]}</b>', reply_markup=await kb_back('project:menu'))
		if resp['project']:
			await state.finish()
			await message.answer(f'<b>Информация о проекте</b>\n├ ID:  <code>{resp["project"]["id"]}</code>\n├ Название:  <code>{resp["project"]["name"]}</code>\n├ Соль:  <code>{resp["project"]["salt"]}</code>\n└ UUID: <code>{resp["project"]["uuid"]}</code>', reply_markup=await kb_project_manage(resp['project']))
		else:
			await message.answer('<b>Поиск проекта</b>\n<b>❌ Не удалось найти проект с задаными параметрами</b>\n<i>Введите ID\\uuid\\название проекта </i>', reply_markup=await kb_back('project:menu'))






@dp.callback_query_handler(text_startswith='key', state='*')
async def handler_key(call: types.CallbackQuery, state: FSMContext, custom_data = None):
	await state.finish()
	cd = custom_data.split(':') if custom_data else call.data.split(':')

	if cd[1] == 'menu':
		await call.message.edit_text('<b>Управление ключами</b>', reply_markup=await kb_key_menu())

	elif cd[1] == 'delete':
		async with httpx.AsyncClient() as client:
			resp = await client.post(f'{website_url}/api/license_key', json={'action': 'delete', 'id': int(cd[2])})

		await call.message.edit_text('<b>Управление ключами</b>', reply_markup=await kb_key_menu())
	
	elif cd[1] == 'create':
		if len(cd) == 2:
			await call.message.edit_text('<b>Создание ключа</b>\n<i>Выберите проект</i>', reply_markup=await kb_key_create(state='select_project'))
		else:
			project_id = int(cd[2])
			await call.message.edit_text('<b>Создание ключа</b>\n<i>Введите срок действия ключа в секундах</i>', reply_markup=await kb_key_create(state='enter_exp_ts'))
			await Key.create.set()
			async with state.proxy() as data:
				data['project_id'] = project_id
				data['state'] = 'exp_ts'
	
	elif cd[1] == 'search':
		await call.message.edit_text('<b>Поиск ключа</b>\n<i>Введите ID\\значение ключа </i>', reply_markup=await kb_back('key:menu'))
		await Key.search.set()

	elif cd[1] == 'change':
		license_key_id = int(cd[2])
		action = cd[3]
		if action == 'exp_ts':
			await call.message.edit_text('<b>Изменение ключа</b>\n<i>Введите срок действия ключа в секундах</i>', reply_markup=await kb_key_change(state='enter_exp_ts'))
			await Key.change.set()
			async with state.proxy() as data:
				data['license_key_id'] = license_key_id
				data['state'] = 'exp_ts'

@dp.message_handler(state=Key.create)
async def Key_create(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		if data['state'] == 'exp_ts':
			mt = message.text
			try: exp_ts = int(mt)
			except: return await message.answer('Введите число без символов')
			data['exp_ts'] = exp_ts
			data['state'] = 'max_conns'
			await message.answer(f'<b>Создание ключа</b>\n└ Срок действия:  <code>{exp_ts}</code> секунд\n<i>Введите максимальное количество подключений</i>', reply_markup=await kb_key_create(state='enter_max_conns'))
		
		elif data['state'] == 'max_conns':
			mt = message.text
			try: max_conns = int(mt)
			except: return await message.answer('Введите число без символов')
			data['max_conns'] = max_conns
			async with httpx.AsyncClient() as client:
				resp = (await client.post(f'{website_url}/api/license_key', json={'action': 'create', 'project_id': data['project_id'], 'max_connections': data['max_conns'], 'exp_ts': int(time.time()) + data['exp_ts']})).json()
				if resp['error']:
					await state.finish()
					return await message.answer(f'Ошибка при создании ключа: <b>{resp["error_desc"]}</b>', reply_markup=await kb_back('key:menu'))
				data['license_key'] = resp['license_key']

			await state.finish()
			await message.answer(f'<b>Ключ создан</b>\n├ ID:  <code>{data["license_key"]["id"]}</code>\n├ Макс. подключений:  <code>{data["license_key"]["max_connections"]}</code>\n├ Активен до:  <code>{datetime.fromtimestamp(data["license_key"]["exp_ts"])}</code>\n└ Значение:  <code>{data["license_key"]["value"]}</code>', reply_markup=await kb_key_manage(data['license_key']))
@dp.callback_query_handler(state=Key.create)
async def Key_create_(call: types.CallbackQuery, state: FSMContext):
	cd = call.data.split(':')
	async with state.proxy() as data:
		if data['state'] == 'exp_ts':
			try: exp_ts = int(cd[0])
			except: return
			data['exp_ts'] = exp_ts
			data['state'] = 'max_conns'
			await call.message.edit_text(f'<b>Создание ключа</b>\n└ Срок действия:  <code>{exp_ts}</code> секунд\n<i>Введите максимальное количество подключений</i>', reply_markup=await kb_key_create(state='enter_max_conns'))
		
		elif data['state'] == 'max_conns':
			try: max_conns = int(cd[0])
			except Exception as e: return await call.answer(f'error: {e}')
			data['max_conns'] = max_conns
			async with httpx.AsyncClient() as client:
				resp = (await client.post(f'{website_url}/api/license_key', json={'action': 'create', 'project_id': data['project_id'], 'max_connections': data['max_conns'], 'exp_ts': int(time.time()) + data['exp_ts']})).json()
				if resp['error']:
					await state.finish()
					return await message.answer(f'Ошибка при создании ключа: <b>{resp["error_desc"]}</b>', reply_markup=await kb_back('key:menu'))
				data['license_key'] = resp['license_key']

			await state.finish()
			await call.message.edit_text(f'<b>Ключ создан</b>\n├ ID:  <code>{data["license_key"]["id"]}</code>\n├ Макс. подключений:  <code>{data["license_key"]["max_connections"]}</code>\n├ Активен до:  <code>{datetime.fromtimestamp(data["license_key"]["exp_ts"])}</code>\n└ Значение:  <code>{data["license_key"]["value"]}</code>', reply_markup=await kb_key_manage(data['license_key']))

@dp.message_handler(state=Key.change)
async def Key_change(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		if data['state'] == 'exp_ts':
			mt = message.text
			try: exp_ts = int(mt)
			except: return await message.answer('Введите число без символов')
			data['exp_ts'] = exp_ts
			async with httpx.AsyncClient() as client:
				resp = (await client.post(f'{website_url}/api/license_key', json={'action': 'update', 'id': data['license_key_id'], 'exp_ts': int(time.time()) + data['exp_ts']})).json()
				resp = (await client.post(f'{website_url}/api/license_key', json={'action': 'get', 'id': data['license_key_id']})).json()
	await state.finish()
	await message.answer(f'<b>Ключ обновлён</b>\n├ ID:  <code>{resp["license_key"]["id"]}</code>\n├ Макс. подключений:  <code>{resp["license_key"]["max_connections"]}</code>\n├ Активен до:  <code>{datetime.fromtimestamp(resp["license_key"]["exp_ts"])}</code>\n└ Значение:  <code>{resp["license_key"]["value"]}</code>', reply_markup=await kb_key_manage(resp['license_key']))
@dp.callback_query_handler(state=Key.change)
async def Key_change_(call: types.CallbackQuery, state: FSMContext):
	cd = call.data.split(':')
	async with state.proxy() as data:
		if data['state'] == 'exp_ts':
			try: exp_ts = int(cd[0])
			except: return
			data['exp_ts'] = exp_ts
			async with httpx.AsyncClient() as client:
				resp = (await client.post(f'{website_url}/api/license_key', json={'action': 'update', 'id': data['license_key_id'], 'exp_ts': int(time.time()) + data['exp_ts']})).json()
				resp = (await client.post(f'{website_url}/api/license_key', json={'action': 'get', 'id': data['license_key_id']})).json()
	await state.finish()
	await call.message.edit_text(f'<b>Ключ обновлён</b>\n├ ID:  <code>{resp["license_key"]["id"]}</code>\n├ Макс. подключений:  <code>{resp["license_key"]["max_connections"]}</code>\n├ Активен до:  <code>{datetime.fromtimestamp(resp["license_key"]["exp_ts"])}</code>\n└ Значение:  <code>{resp["license_key"]["value"]}</code>', reply_markup=await kb_key_manage(resp['license_key']))



@dp.message_handler(state=Key.search)
async def Key_search(message: types.Message, state: FSMContext):
	mt = message.text.strip()
	async with httpx.AsyncClient() as client:
		payload = {'action': 'get', 'value': mt}
		if mt.isdigit(): payload['id'] = mt
		resp = (await client.post(f'{website_url}/api/license_key', json=payload)).json()
		if resp['error']:
			await state.finish()
			return await message.answer(f'Ошибка при поиске ключа: <b>{resp["error_desc"]}</b>', reply_markup=await kb_back('key:menu'))
		if resp['license_key']:
			await state.finish()
			await message.answer(f'<b>Информация о ключе</b>\n├ ID:  <code>{resp["license_key"]["id"]}</code>\n├ Макс. подключений:  <code>{resp["license_key"]["max_connections"]}</code>\n├ Активен до:  <code>{datetime.fromtimestamp(resp["license_key"]["exp_ts"])}</code>\n└ Значение:  <code>{resp["license_key"]["value"]}</code>', reply_markup=await kb_key_manage(resp['license_key']))
		else:
			await message.answer('<b>Поиск ключа</b>\n<b>❌ Не удалось найти ключа с задаными параметрами</b>\n<i>Введите ID\\значение ключа</i>', reply_markup=await kb_back('key:menu'))



















@dp.callback_query_handler(text_startswith='utils', state='*')
async def handler_utils(call: types.CallbackQuery, state: FSMContext, custom_data = None):
	cd = custom_data.split(':') if custom_data else call.data.split(':')

	if cd[1] == 'menu':
		await call.message.edit_text(text=f'<b>Меню управления криптом</b>', reply_markup=await kb_menu())

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