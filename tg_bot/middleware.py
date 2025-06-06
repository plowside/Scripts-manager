from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram import types, Dispatcher
from aiogram.types import Message,Update
from aiogram.utils.exceptions import Throttled

import asyncio, json

from config import *



limit = antiflood_limit

def rate_limit(limit: int, key=None):
	def decorator(func):
		setattr(func, "throttling_rate_limit", limit)
		if key:
			setattr(func, "throttling_key", key)
		return func

	return decorator

class ThrottlingMiddleware(BaseMiddleware):
	def __init__(self, limit=limit, key_prefix='antiflood_'):
		self.rate_limit = limit
		self.prefix = key_prefix
		super(ThrottlingMiddleware, self).__init__()

	async def on_process_message(self, message: Message, data: dict):
		handler = current_handler.get()
		dispatcher = Dispatcher.get_current()

		if handler:
			limit = getattr(handler, "throttling_rate_limit", self.rate_limit)
			key = getattr(handler, "throttling_key", f"{self.prefix}_{handler.__name__}")
		else:
			limit = self.rate_limit
			key = f"{self.prefix}_message"


		if message.from_user.id not in admin_ids:
			try:
				await dispatcher.throttle(key, rate=limit)
			except Throttled as t:
				await self.message_throttled(message, t)
				raise CancelHandler()

	@staticmethod
	async def message_throttled(message: types.Message, throttled: Throttled):
		if throttled.exceeded_count <= 2:
			await message.reply(antiflood_text)