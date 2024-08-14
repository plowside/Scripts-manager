import threading, traceback, asyncio, logging, httpx, random, time, json, os
from cashews import cache

from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta, timezone

from loader import bot
from config import *

#################################################################################################################################
async def kb_construct(keyboard = None, query = {}, row_width = 2):
	if not keyboard: keyboard = InlineKeyboardMarkup(row_width)
	if type(query) is dict:
		for x in query:
			_ = query[x].split('^')
			if _[0] == 'url': keyboard.insert(InlineKeyboardButton(x,url=_[1]))

			elif _[0] == 'cd': keyboard.insert(InlineKeyboardButton(x,callback_data=_[1]))
	else:
		for x in query: keyboard.insert(x)

	return keyboard

async def kb_close():
	keyboard = await kb_construct(InlineKeyboardMarkup(), {'❌ Закрыть':'cd^utils:delete'})

	return keyboard
#################################################################################################################################
logging.getLogger("httpx").setLevel(logging.ERROR)
cache.setup("mem://")

# Получить информацию о пользователе из объекта types.Message | types.CallbackQuery
def get_user(data):
	return [data.from_user.id, (data.from_user.username.lower() if data.from_user.username is not None else None), data.from_user.first_name]

def format_user_url(uid = None, username = None, first_name = None, user_db = None):
	if user_db:
		uid = user_db['uid']; username = user_db['username']; first_name = user_db['first_name']
	first_name = 'without_first_name' if first_name in ('', None) else first_name
	return f'<a href="{username}.t.me">{first_name}</a>' if username else f'<a href="tg://user?id={uid}">{first_name}</a>'


# Удаление какого либо файла
def os_delete(*paths):
	for path in paths:
		for x in range(50):
			try: os.remove(path); break
			except: time.sleep(.8)

# Удалить одно/несколько сообщений
async def delmsg(*messages):
	for x in messages:
		try:
			if isinstance(x, dict): await bot.delete_message(x['chat_id'], x['message_id'])
			else: await x.delete()
		except Exception as e: logging.debug(f'Ошибка при удалении сообщения: {e}')

# Отправление сообщения всем админам
async def admin_spam(text, reply_markup = None):
	for x in admin_ids:
		try: await bot.send_message(x, text, reply_markup=reply_markup if reply_markup else await kb_close(), disable_web_page_preview=True)
		except Exception as e: logging.error(f'Error on admin_spam[user_id: {x}]: {e}')






async def get_random_fact():
	async with httpx.AsyncClient() as client:
		resp = await client.get('https://uselessfacts.jsph.pl/api/v2/facts/random?language=ru')
		try: 
			return resp.json()['text']
		except: return 'Не удалось получить факт. Попробуйте позже.'


############################## ФОРМАТИРОВАНИЕ ТЕКСТА|ДАННЫХ ##############################
def timeFormat(time):
	if time <= 7200:
		time = int(time/60)
		return (time, morpher(time, 'минут'))
	elif time <= 86400: return (time/3600, morpher(int(time/3600), 'часов'))
	else: 
		return (time/86400, morpher(int(time/86400), 'дней'))

def r_format(_):
	return '{:,}'.format(_)

def morpher(num, presset = 'час', cases = None):
	pressets = {
		'днейднядень': {'nom': 'день', 'gen': 'дня', 'plu': 'дней'},
		'часовчасычас': {'nom': 'час', 'gen': 'часа', 'plu': 'часов'},
		'минутминутыминута': {'nom': 'минута', 'gen': 'минуты', 'plu': 'минут'},
		'секундсекундысекунда': {'nom': 'секунда', 'gen': 'секунды', 'plu': 'секунд'},
		'сервисовсервисасервис': {'nom': 'сервис', 'gen': 'сервиса', 'plu': 'сервисов'},
		'рублейрублярубль': {'nom': 'рубль', 'gen': 'рубля', 'plu': 'рублей'},
		'задачзадачизадача': {'nom': 'задача', 'gen': 'задачи', 'plu': 'задач'},
		'номеровномераномер': {'nom': 'номер', 'gen': 'номера', 'plu': 'номеров'}
	}
	if cases == None:
		cases = [pressets[x] for x in pressets if presset in x][0]

	z = {0:'nom', 1:'gen', 2:'plu'}
	if type(cases) is not dict:
		cases_ = cases
		cases = {}
		for i, x in enumerate(cases_):
			cases[z[i]] = x
	num = abs(num)
	word = ''
	if '.' in str(num):
		word = cases['gen']
	else:
		last_two_digits = num % 100
		last_digit = num % 10

		if (last_digit >= 2 and last_digit <= 4 and last_two_digits >= 20):
			word = cases['gen']
		elif (last_digit >= 2 and last_digit <= 4 and last_two_digits <= 10):
			word = cases['gen']
		elif (last_digit == 1 and last_two_digits != 11) or (last_digit >= 2 and last_digit <= 4 and (last_two_digits < 10 or last_two_digits >= 20)):
			word = cases['nom']
		else:
			word = cases['plu']

	return word