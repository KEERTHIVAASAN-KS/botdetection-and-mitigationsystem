from fastapi import FastAPI,Request
from detectionengine.botdetector import detect_bot,detect_bot_fp,finalscore


app=FastAPI(title="bot detection and mitigation system")

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
        
     


