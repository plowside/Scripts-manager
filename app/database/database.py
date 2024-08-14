import asyncio, asyncpg, json

from datetime import datetime
from typing import Optional, List, Dict, Any

from .models import *
from ..api.models import *
from ..config import settings


class AsyncPostgresDB:
	def __init__(self):
		self.pool = None
		self.Project = Project
		self.LicenseKey = LicenseKey

	async def init_pool(self):
		self.pool = await asyncpg.create_pool(
			user=settings.database.user,
			password=settings.database.password,
			database=settings.database.database,
			host=settings.database.host,
			port=settings.database.port
		)
		await self.create_tables()

	async def close_pool(self):
		await self.pool.close()

	async def create_tables(self):
		async with self.pool.acquire() as conn:
			await conn.execute('''
				CREATE TABLE IF NOT EXISTS project(
					id SERIAL PRIMARY KEY,
					uuid VARCHAR(50) NOT NULL,
					name VARCHAR(50) NOT NULL,
					salt VARCHAR(100) NOT NULL,
					create_ts BIGINT NOT NULL
				)
			''')
			await conn.execute('''
				CREATE TABLE IF NOT EXISTS license_key(
					id SERIAL PRIMARY KEY,
					project_id INTEGER,
					value VARCHAR(100),
					max_connections INTEGER NOT NULL,
					exp_ts BIGINT NOT NULL,
					create_ts BIGINT NOT NULL
				)
			''')
			await conn.execute('''
				CREATE TABLE IF NOT EXISTS license_key_connections(
					id SERIAL PRIMARY KEY,
					license_key_id INTEGER,
					mac VARCHAR(100) NOT NULL,
					hwid VARCHAR(100),
					create_ts BIGINT NOT NULL
				)
			''')

	@staticmethod
	def format_sql(**kwargs):
		i = 1
		query = []
		values = []
		for x in kwargs:
			if not kwargs[x]: continue
			query.append(f"{x} = ${i}")
			values.append(kwargs[x])
			i+=1
		return ', '.join(query), values


	async def release_connection(self, conn):
		await self.pool.release(conn)

	async def execute(self, query: str, *args):
		async with self.pool.acquire() as conn:
			result = await conn.execute(query, *args)
		return result

	async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
		async with self.pool.acquire() as conn:
			result = await conn.fetch(query, *args)
		return [dict(record) for record in result]

	async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
		async with self.pool.acquire() as conn:
			result = await conn.fetchrow(query, *args)
		return dict(result) if result else None

	async def fetchval(self, query: str, *args) -> Optional[Any]:
		async with self.pool.acquire() as conn:
			result = await conn.fetchval(query, *args)
		return result

db = AsyncPostgresDB()