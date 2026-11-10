from fastapi import FastAPI,Request,Response,HTTPException
from detectionandmitigationengine.detectionandmitigation import detect_bot_fp
from log_collector.logcollector import collectlogs
from detectionandmitigationengine.detectionandmitigation import detect_and_mitigate
from contextlib import asynccontextmanager
import asyncio 
import redis.asyncio as redis
from models.model import modelpredict
import os
import secrets
from pathlib import Path
from fastapi.staticfiles import StaticFiles


SESSION_EXPIRY=1800



@asynccontextmanager
async def lifespanfunction(app:FastAPI):
    # Keep Redis configurable so the same API works with the local Docker
    # port and with a Redis service in another environment.
    redisclient=redis.Redis(
        host=os.getenv("REDIS_HOST", "127.0.0.1"),
        port=int(os.getenv("REDIS_PORT", "1234")),
        db=0,
        decode_responses=True,
    )
    await redisclient.ping()
    app.state.redisclient = redisclient

    # The local mouse demo does not require Nginx. Enable this worker only
    # when an Nginx JSON access log is available in the environment.
    logtask = None
    if os.getenv("ENABLE_NGINX_LOG_COLLECTOR", "false").lower() == "true":
        logtask=asyncio.create_task(collectlogs())
    detectionandmitigationtask=asyncio.create_task(detect_and_mitigate(redisclient))

    yield 

    if logtask:
        logtask.cancel()
    detectionandmitigationtask.cancel()

    tasks = [detectionandmitigationtask]
    if logtask:
        tasks.append(logtask)
    await asyncio.gather(*tasks,return_exceptions=True)
    await redisclient.aclose()

app=FastAPI(title="bot detection and mitigation system",lifespan=lifespanfunction)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")


@app.post("/session")
async def create_session():
    """Issue an unpredictable correlation ID for the browser demo.

    This ID ties the mouse score to the rest of a session; it is not an
    authentication credential.
    """
    return {"sessionid": secrets.token_urlsafe(24)}

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
    """Score one browser mouse summary and keep its risk with the session."""
    try:
        data=await req.json()
        sessionid=str(data["sessionid"])
        features=data["features"]
        result=modelpredict(features,"mouse")
        await updatescore(req,sessionid,"rmouse",result)
        return {"sessionid": sessionid, "mouse_risk": result}
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Invalid mouse payload: {exc}") from exc
        
@app.post("/fingerprint")
async def fingerprintlayer(req:Request):
    data=await req.json()
    sessionid=data["sessionid"]
    httpua=req.headers.get("user-agent","")
    acceptlang=req.headers.get("accept-language","")
    features=data["features"]
    result=detect_bot_fp(features,httpua,acceptlang)
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
        

        
     


