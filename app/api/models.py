from pydantic import BaseModel

class ProjectPayload(BaseModel):
	action: str = None
	id: int = None
	name: str = None

class LicenseKeyPayload(BaseModel):
	action: str = None
	id: int = None
	project_id: int = None
	value: str = None
	exp_ts: int = None

	key: str = None