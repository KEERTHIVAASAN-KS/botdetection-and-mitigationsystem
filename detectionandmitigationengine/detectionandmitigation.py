import asyncio 

#expected fingerprint features
"""
{
    "webdriver": false,
    "user_agent": "Mozilla/5.0 ...",
    "platform": "Win32",
    "language": "en-US",
    "webgl_renderer": "ANGLE (NVIDIA ...)",
    "automation_flags": {
        "selenium": false,
        "playwright": false,
        "puppeteer": false
    },
    "browser_apis": {
        "canvas": true,
        "webgl": true,
        "local_storage": true,
        "session_storage": true,
        "indexeddb": true
    }
}
"""
 
def detect_bot_fp(data,http_user_agent,accept_language):
    score=0
    if data["webdriver"] is True:
        score+=30 
    automationflags=data.get("automation_flags",{})
    if any(automationflags.values()):
        score+=25
    js_ua=data.get("user_agent","")
    #headless browser detection
    if "headlesschrome" in js_ua.lower():
        score+=20
    #js ua and http ua mismatch
    if js_ua and http_user_agent and js_ua.strip()!=http_user_agent.strip():
        score+=20
    jslanguage=data.get("language","")
    if jslanguage and accept_language:
        browserlang=jslanguage.split("-")[0].lower()
        headerlang=jslanguage.split(",")[0].split("-")[0].lower()
        if browserlang!=headerlang:
            score+=10
     # Rule 6: Platform vs User-Agent OS mismatch
    platform=data.get("platform","").lower()
    ua=js_ua.lower()

    if platform and ua:
        if "win" in platform and "windows" not in ua:
            score+=10

        elif "mac" in platform and "mac os" not in ua and "macintosh" not in ua:
            score+=10

        elif "linux" in platform and "linux" not in ua and "android" not in ua:
            score+=10

        elif ("iphone" in platform or "ipad" in platform) and "iphone" not in ua and "ipad" not in ua:
            score+=10

    # Rule 7: Software WebGL renderer
    renderer=data.get("webgl_renderer","").lower()
    software_renderers=["swiftshader","llvmpipe","software rasterizer"]
    if any(item in renderer for item in software_renderers):
        score+=8

    # Rule 8: Expected browser APIs unavailable
    browser_apis=data.get("browser_apis",{})
    
    unavailable=sum(value is False for value in browser_apis.values())

    if unavailable >= 3:
        score+=5

    
    score=min(score, 100)
    return score/100
    
    
    

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

