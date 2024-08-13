import datetime, asyncio, asyncpg, shutil, json, os

from fastapi import APIRouter, Depends, HTTPException, Cookie, Request, Response, status
from typing import Annotated, Union

from .services import *
from .models import *


router = APIRouter(
	prefix="/api",
	tags=["api"]
)



@router.post('/project')
async def project(payload: ProjectPayload):
	action = payload.action
	try:
		match action:
			case 'create':
				create_project = await Project.create(name=payload.name)
				return {'error': False, 'project': create_project}

			case 'get':
				get_project = await Project.get(id=payload.id, name=payload.name)
				return {'error': False, 'project': get_project}

			case 'update':
				update_project = await Project.update(id=payload.id, name=payload.name)
				get_project = await Project.get(id=payload.id)
				return {'error': False, 'project': create_project}

			case _:
				return {'error': True, 'error_msg': 'Invalid action'}
	except Exception as e:
		return {'error': True, 'error_msg': str(e)}

@router.post('/license_key')
async def license_key(payload: LicenseKeyPayload):
	action = payload.action
	try:
		match action:
			case 'create':
				create_license_key = await LicenseKey.create(project_id=payload.project_id, exp_ts=payload.exp_ts)
				return {'error': False, 'license_key': create_license_key}

			case 'get':
				get_license_key = await LicenseKey.get(project_id=payload.project_id, id=payload.id, value=payload.value)
				license_key_connection = await LicenseKey.activate()
				return {'error': False, 'license_key': get_license_key}

			case 'update':
				update_license_key = await LicenseKey.update(id=payload.id, name=payload.name)
				get_license_key = await LicenseKey.get(id=payload.id)
				return {'error': False, 'license_key': create_license_key}

			case 'check':
				decrypted_payload = await LicenseKey.decrypt(encrypted_payload=payload.key, key=settings.default_salt)
				this_license_key, this_mac, this_hwid = decrypted_payload.split(':')
				this_hwid = None if this_hwid == '' else this_hwid
				get_license_key = await LicenseKey.get(value=this_license_key)
				if not get_license_key:
					return {'error': True, 'error_msg': 'invalid_license_key', 'error_desc': 'Недействительный ключ активации'}
				elif get_license_key.exp_ts <= await ts():
					return {'error': True, 'error_msg': 'expired_license_key', 'error_desc': 'Просроченный ключ активации'}

				verify_license_key = await LicenseKey.verify(license_key=get_license_key, mac=this_mac, hwid=this_hwid)
				if not verify_license_key[0]:
					return {'error': True, 'error_msg': verify_license_key[1], 'error_desc': verify_license_key[2]}

				get_project = await Project.get(id=get_license_key.project_id)
				return {'error': False, 'pyarmor_key': await LicenseKey.encrypt(plain_payload=f'{get_project.id}-{get_project.create_ts}:{get_license_key.id}-{get_license_key.create_ts}:{await ts()}-{get_license_key.exp_ts}:{verify_license_key[1]}-{verify_license_key[2]}', key=get_project.salt.encode())}
			case _:
				return {'error': True, 'error_msg': 'Invalid action'}
	except Exception as e:
		return {'error': True, 'error_msg': str(e)}