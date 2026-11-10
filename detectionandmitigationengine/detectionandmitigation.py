import asyncio 

 
def detect_bot_fp(data):
    return None

def finalscore(scores):
    weights={"session":0.4,"fp":0.35,"mouse":0.25}
    finalscore=(scores["rsession"]*weights["session"])+(scores["rmouse"]*weights["mouse"])+(scores["rfp"]*weights["fp"])
    if finalscore<0.3:
        return finalscore,"low"
    elif finalscore>=0.3 and finalscore<0.7:
        return finalscore,"medium"
    else:
        return finalscore,"high"



async def detect_and_mitigate(redisclient):
    while True:
        async for key in redisclient.scan_iter(match="*_scores"):
            sessionid=key.removesuffix("_scores")
            scores=await redisclient.hgetall(key)
            required=["rsession","rmouse","rfp"]
            if not all(field in scores for field in required):
                continue 
            scores={field:float(scores[field]) for field in required}
            score,cat=finalscore(scores)
            action=None
            if cat=="low":
                action="allow"
            if cat=="medium":
                action="challenge"
            if cat=="high":
                action="block"
            await redisclient.hset(f"{sessionid}_decision","action",action)        
    
            
        await asyncio.sleep(2)

