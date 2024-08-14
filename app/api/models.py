from pydantic import BaseModel
from fastapi import FastAPI, Form, Depends, UploadFile

class ProjectPayload(BaseModel):
	action: str = None
	id: int = None
	name: str = None
	uuid: str = None

class LicenseKeyPayload(BaseModel):
	action: str = None
	id: int = None
	project_id: int = None
	value: str = None
	max_connections: int = None
	exp_ts: int = None

	key: str = None