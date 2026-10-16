"""Separate local sink. Stores only redacted receipt metadata in memory."""
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from .security import SECRET

app = FastAPI(title='AgentShield isolated synthetic receiver')
receipts = []
class Payload(BaseModel):
    model_config = ConfigDict(extra='forbid')
    payload: str = Field(max_length=16384)
@app.post('/receive')
async def receive(body: Payload, request: Request):
    if request.client.host not in ('127.0.0.1', '::1', 'testclient'):
        raise HTTPException(403, 'Loopback only')
    result = {'received': True, 'synthetic_secret_received': SECRET in body.payload, 'bytes': len(body.payload.encode())}
    receipts.append(result)
    return result
