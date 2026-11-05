from fastapi import FastAPI,Request

app=FastAPI(title="bot detection and management system")

scores={r_mouse:None,r_http:None,r_fp:None}

@app.post("/http")
async def httplayer(req:Request):
    data= await req.json()
    scores["r_http"]=httpmodel(data)
    verdict=detection_engine(scores)
    mitigation_engine(verdict)    
    

@app.post("/mouse")
async def mouselayer(req:Request):
    data= await req.json()
    scores["r_mouse"]=mousemodel(data)
    
@app.post("/fingerprint")
async def fingerprintlayer(req:Request):
    data=await req.json()
    scores["r_fp"]=fingerprintmodel(data)
        
     


