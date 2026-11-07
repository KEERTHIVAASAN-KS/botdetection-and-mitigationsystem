from fastapi import FastAPI,Request
from detectionengine.botdetector import detect_bot,detect_bot_fp
from log_collector.logcollector import collectlogs
from mitigation_engine.mitigation import mitigate
from contextlib import asynccontextmanager
import asyncio 

@asynccontextmanager
async def lifespanfunction(app:FastAPI):
    logtask=asyncio.create_task(collectlogs())
    mitigationtask=asyncio.create_task(mitigate())

    yield 

    logtask.cancel()
    mitigationtask.cancel()

    await asyncio.gather(logtask,mitigationtask,return_exceptions=True)

app=FastAPI(title="bot detection and mitigation system",lifespan=lifespanfunction)

results={"rmouse":0,"rsession":0,"rfp":0}

@app.post("/http")
async def httplayer(req:Request):
    data=await req.json()
    results["rsession"]=detect_bot(data,"session")
    

@app.post("/mouse")
async def mouselayer(req:Request):
    data=await req.json()
    results["rmouse"]=detect_bot(data,"mouse")
    
@app.post("/fingerprint")
async def fingerprintlayer(req:Request):
    data=await req.json()
    results["rfp"]=detect_bot_fp(data)
        
     


