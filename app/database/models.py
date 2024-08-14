from pydantic import BaseModel

class Project(BaseModel):
	id: int
	name: str
	uuid: str
	salt: str
	create_ts: int

class LicenseKey(BaseModel):
	id: int
	project_id: int
	value: str
	max_connections: int
	exp_ts: int
	create_ts: int

class LicenseKeyConnections(BaseModel):
	id: int
	license_key_id: int
	mac: str
	hwid: int
	create_ts: int