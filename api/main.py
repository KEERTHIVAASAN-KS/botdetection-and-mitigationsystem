from fastapi import FastAPI,Request,Response
from detectionandmitigationengine.detectionandmitigation import detect_bot_fp
from log_collector.logcollector import collectlogs
from detectionandmitigationengine.detectionandmitigation import detect_and_mitigate
from contextlib import asynccontextmanager
import asyncio 
import redis.asyncio as redis
from models.model import modelpredict


SESSION_EXPIRY=1800



@asynccontextmanager
async def lifespanfunction(app:FastAPI):
    redisclient=redis.Redis(host="127.0.0.1",port=1234,db=0,decode_responses=True)
    
    
    logtask=asyncio.create_task(collectlogs())
    detectionandmitigationtask=asyncio.create_task(detect_and_mitigate(redisclient))

    yield 

    logtask.cancel()
    detectionandmitigationtask.cancel()

    await asyncio.gather(logtask,detectionandmitigationtask,return_exceptions=True)
    await redisclient.aclose()

app=FastAPI(title="bot detection and mitigation system",lifespan=lifespanfunction)

async def updatescore(req: Request, session_id: str, field: str, score):
    redisclient=req.app.state.redisclient
    key = f"{session_id}_scores"
    await redisclient.hset(key,field,str(score))
    await redisclient.expire(key,SESSION_EXPIRY)



@app.post("/http")
async def httplayer(req:Request):
    data=await req.json()
    sessionid=data["sessionid"]
    features=data["features"]
    result=modelpredict(features,"session")
    await updatescore(req,sessionid,"rsession",result)

    

@app.post("/mouse")
async def mouselayer(req:Request):
    data=await req.json()
    sessionid=data["sessionid"]
    features=data["features"]
    result=modelpredict(features,"mouse")
    await updatescore(req,sessionid,"rmouse",result)
        
@app.post("/fingerprint")
async def fingerprintlayer(req:Request):
    data=await req.json()
    sessionid=data["sessionid"]
    features=data["features"]
    result=detect_bot_fp(features)
    await updatescore(req,sessionid,"rfp",result)

@app.get("/nginxenforcement")
async def enforcement(req:Request):
    sessionid=req.headers.get("session-id")
    redisclient=req.app.state.redisclient
    action=await redisclient.hget(f"{sessionid}_decision","action")
    if action=="allow":
        return Response(status_code=204)
    elif action=="challenge":
        return Response(status_code=401)
    elif action=="block":
        return Response(status_code=403)

    #no decision available
    return Response(status_code=204)
        

        
     


