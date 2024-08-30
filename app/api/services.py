import subprocess, datetime, aiofiles, aiofiles.os, asyncio, zipfile, hashlib, pathlib, string, random, shutil, uuid, time, os

from fastapi import File, UploadFile
from cryptography.fernet import Fernet

from .models import *
from ..database import *
from ..config import settings




async def ts():
	return int(time.time())

async def gen_key(length = 32):
	return ''.join(random.choices(string.ascii_lowercase, k=length)).upper()

async def gen_name():
	return ''.join(random.choices(string.ascii_lowercase, k=16))



class Project:
	@staticmethod
	async def create(name: str = None):
		try:
			if name:
				get_project = await Project.get(name=name)
				if get_project:
					name = await gen_name()
			else:
				name = await gen_name()
			this_ts = await ts()
			this_uuid = str(uuid.uuid4())
			salt = await Project.gen_salt()
			await db.execute('INSERT INTO project(name, uuid, salt, create_ts) VALUES ($1, $2, $3, $4)', name, this_uuid, salt, this_ts)
			return await Project.get(name=name)
		except Exception as e:
			raise e

	@staticmethod
	async def get(id: int = None, name: str = None, uuid: str = None, all: bool = False):
		try:
			if id or name or uuid:
				get_project = await db.fetchrow('SELECT * FROM project WHERE id = $1 OR name = $2 OR uuid = $3', id, name, uuid)
				if get_project:
					return db.Project(**get_project)
			elif all:
				return await db.fetch('SELECT * FROM project ORDER BY create_ts DESC')
			return None
		except Exception as e:
			raise e

	@staticmethod
	async def update(id: int, name: str):
		try:
			await db.execute('UPDATE project SET name = $1 WHERE id = $2', name, id)
			return True
		except Exception as e:
			raise e

	@staticmethod
	async def delete(id: int):
		try:
			await db.execute('DELETE FROM project WHERE id = $1', id)
			return True
		except Exception as e:
			raise e


	@staticmethod
	async def gen_salt():
		generated_salt = await asyncio.get_running_loop().run_in_executor(None, Fernet.generate_key)
		return generated_salt.decode()





class LicenseKey:
	@staticmethod
	async def create(project_id: int, max_connections: int = 1, exp_ts: int = None, timedelta: datetime.timedelta = None):
		try:
			get_project = await Project.get(id=project_id)
			if not get_project:
				return False

			value = await gen_key()
			this_ts = await ts()

			if timedelta:
				exp_ts = (datetime.datetime.fromtimestamp(this_ts) + timedelta).timestamp()
			
			await db.execute('INSERT INTO license_key(project_id, value, max_connections, exp_ts, create_ts) VALUES ($1, $2, $3, $4, $5)', get_project.id, value, max_connections, exp_ts, this_ts)
			return await LicenseKey.get(value=value)
		except Exception as e:
			raise e

	@staticmethod
	async def get(project_id: int = None, id: int = None, value: str = None):
		try:
			if project_id:
				return await db.fetch('SELECT * FROM license_key WHERE project_id = $1', project_id)
			elif id or value:
				get_license_key = await db.fetchrow('SELECT * FROM license_key WHERE id = $1 OR value = $2', id, value)
				if get_license_key:
					return db.LicenseKey(**get_license_key)
			return None
		except Exception as e:
			raise e

	@staticmethod
	async def update(id: int, exp_ts: int):
		try:
			await db.execute('UPDATE license_key SET exp_ts = $1 WHERE id = $2', exp_ts, id)
			return True
		except Exception as e:
			raise e

	@staticmethod
	async def delete(id: int):
		try:
			await db.execute('DELETE FROM license_key WHERE id = $1', id)
			return True
		except Exception as e:
			raise e

	@staticmethod
	async def activate(license_key_id: int, mac: str, hwid: str = None):
		try:
			await db.execute('INSERT INTO license_key_connections(license_key_id, mac, hwid, create_ts) VALUES ($1, $2, $3, $4)', license_key_id, mac, hwid, await ts())
			return True
		except Exception as e:
			raise e

	@staticmethod
	async def verify(license_key: db.LicenseKey, mac: str, hwid: str = None):
		try:
			async with db.pool.acquire() as conn:
				license_key_connections = await conn.fetch('SELECT * FROM license_key_connections WHERE license_key_id = $1', license_key.id)
				valid = len([x for x in license_key_connections if x['mac'] == mac]) > 0
				if valid:
					get_connection = await conn.fetchrow('SELECT * FROM license_key_connections WHERE license_key_id = $1', license_key.id)
					return (True, mac, hwid)
				elif not valid and len(license_key_connections) < license_key.max_connections:
					activated = await LicenseKey.activate(license_key.id, mac, hwid)
					get_connection = await conn.fetchrow('SELECT * FROM license_key_connections WHERE license_key_id = $1', license_key.id)
					return (True, mac, hwid)
				elif not valid and len(license_key_connections) >= license_key.max_connections:
					return (False, 'too_many_connections', 'Достигнуто максимальное количество устройств')
				else:
					return (False, 'unknown_error', 'Неизвестная ошибка')

			return None
		except Exception as e:
			raise e

	
	@staticmethod
	async def decrypt(encrypted_payload, key):
		decrypted_text = await asyncio.get_running_loop().run_in_executor(None, Fernet(key).decrypt, encrypted_payload.encode())
		return decrypted_text.decode()

	@staticmethod
	async def encrypt(plain_payload, key):
		encrypted_text = await asyncio.get_running_loop().run_in_executor(None, Fernet(key).encrypt, plain_payload.encode())
		return encrypted_text.decode()






class EncryptSystem:
	def __init__(self, project_file: UploadFile = File(...), project_uuid: str = None):
		self.project_file = project_file
		self.project_uuid = project_uuid if project_uuid else str(uuid.uuid4())
		self.zip_path = f'app/storage/{self.project_uuid}'
		self.temp_path = f'{self.zip_path}_temp'
		self.extract_path = f'{self.zip_path}_ext'

	async def extract_and_find_py_files(self): 
		if self.project_file:
			contents = await self.project_file.read()
			async with aiofiles.open(self.temp_path, 'wb') as file:
				await file.write(contents)

		await asyncio.get_running_loop().run_in_executor(None, lambda: zipfile.ZipFile(self.temp_path).extractall(self.extract_path))
		try: await aiofiles.os.remove(self.temp_path)
		except: ...
		py_files_dict = {}
		
		async def renamed(dirpath, names):
			new_names = [old.encode('cp437').decode('cp866') for old in names]
			for old, new in zip(names, new_names):
				try: await aiofiles.os.rename(os.path.join(dirpath, old), os.path.join(dirpath, new))
				except: ...
			return new_names

		for dirpath, dirs, files in os.walk(self.extract_path, topdown=True):
			await renamed(dirpath, files)
			dirs[:] = await renamed(dirpath, dirs)
		for root, dirs, files in os.walk(self.extract_path):
			rel_root = os.path.relpath(root, self.extract_path)
			py_files = [f for f in files if f.endswith('.py')]
			if py_files:
				if rel_root == '.':
					for f in py_files:
						py_files_dict[f] = 0
				else:
					if rel_root not in py_files_dict:
						py_files_dict[rel_root] = {}
					for f in py_files:
						py_files_dict[rel_root][f] = 0
		return py_files_dict

	async def process_and_encrypt_files(self, files_to_encrypt: dict, project_salt: str):
		async with aiofiles.open('app/templates/encrypt_armor.py', 'r', encoding='utf-8') as template_file:
			template_code = await template_file.read()
		
		template_code = template_code.replace('here_website_url', settings.website_url).replace('here_project_uuid', self.project_uuid).replace('here_fernet_default_key', settings.default_salt).replace('here_fernet_project_key', project_salt)
		for path, content in files_to_encrypt.items():
			if isinstance(content, dict):
				for file_name, action in content.items():
					file_path = os.path.join(self.extract_path, path, file_name)
					await self.handle_file_encryption(file_path, action, template_code)
			else:
				file_path = os.path.join(self.extract_path, path)
				await self.handle_file_encryption(file_path, content, template_code)

		dist_path = os.path.join('dist')
		if os.path.exists(dist_path):
			for item in os.listdir(dist_path):
				src = os.path.join(dist_path, item)
				dst = os.path.join(self.extract_path, item)
				await aiofiles.os.replace(src, dst)
			await asyncio.get_running_loop().run_in_executor(None, shutil.rmtree, dist_path)

		zip_filename = await asyncio.get_running_loop().run_in_executor(None, self.create_zip_archive, self.extract_path)
		await asyncio.get_running_loop().run_in_executor(None, shutil.rmtree, self.extract_path, True)

		return zip_filename


	async def handle_file_encryption(self, file_path, action, template_code):
		match action:
			case 1:
				process = await asyncio.create_subprocess_shell(f'pyarmor gen --platform linux.x86_64,windows.x86_64 {file_path}')
				await process.communicate()
			case 2:
				async with aiofiles.open(file_path, 'r', encoding='utf-8') as original_file:
					original_code = await original_file.read()
				
				modified_code = f'{template_code}\n\n\n\n{original_code}'.replace('asyncio.run(', '__loop.run_until_complete(')
				
				async with aiofiles.open(file_path, 'w', encoding='utf-8') as modified_file:
					await modified_file.write(modified_code)
				
				process = await asyncio.create_subprocess_shell(f'pyarmor gen --platform linux.x86_64,windows.x86_64 {file_path}')
				await process.communicate()

	def create_zip_archive(self, directory: str):
		with zipfile.ZipFile(self.zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
			for root, dirs, files in os.walk(directory):
				for dir in dirs:
					dir_path = os.path.join(root, dir)
					if not os.listdir(dir_path):
						rel_path = os.path.relpath(dir_path, directory) + '/'
						zipf.write(dir_path, rel_path)

				for file in files:
					file_path = os.path.join(root, file)
					rel_path = os.path.relpath(file_path, directory)
					zipf.write(file_path, rel_path, compress_type=zipfile.ZIP_DEFLATED)

		return self.zip_path