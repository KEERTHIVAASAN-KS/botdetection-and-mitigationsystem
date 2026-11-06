from models.model import modelpredict 


def finalscore(scores):
    weights={"session":0.4,"fp":0.35,"mouse":0.25}
    finalscore=(scores["rsession"]*weights["session"])+(scores["rmouse"]*weights["mouse"])+(scores["rfp"]*weights["fp"])
    if finalscore<0.3:
        return "low"
    elif finalscore>=0.3 and finalscore<0.7:
        return "medium"
    else:
        return "high"


def detect_bot_fp(data):
    return None


def detect_bot(method,data):
    if method=="session":
        result=modelpredict(data,"session")
    if method=="mouse":
        result=modelpredict(data,"mouse")
    return result 


    