import asyncio
from collections import Counter
import json
import aiofiles 
import redis.asyncio as redis 
import  httpx 

def calculatehttpfeatures(requests):
    total=len(requests)
    if total==None:
        return None 
    timestamps=[]
    for r in requests:
        timestamps.append(float(r["timestamp"]))
    totalduration=max(timestamps)-min(timestamps)
    avgtime=(totalduration/(total-1)if total > 1 else 0)
    requestcounts=Counter((r["path"], r["method"]) for r in requests)
    repeated_count=sum(count - 1 for count in requestcounts.values())
    repeated_requests = repeated_count / total
    status_counts=Counter(int(r["status_code"]) // 100 for r in requests)
    method_counts = Counter(r["method"].upper() for r in requests)
    features={
        "NUMBER_OF_REQUESTS":total,
        "TOTAL_DURATION":totalduration,
        "AVERAGE_TIME":avgtime,
        "REPEATED_REQUESTS":repeated_requests,

        "HTTP_RESPONSE_2XX":status_counts[2]/total,
        "HTTP_RESPONSE_3XX":status_counts[3]/total,
        "HTTP_RESPONSE_4XX":status_counts[4]/total,
        "HTTP_RESPONSE_5XX":status_counts[5]/total,

        "GET_METHOD": method_counts["GET"]/total,
        "POST_METHOD": method_counts["POST"]/total,
        "HEAD_METHOD": method_counts["HEAD"]/total,

        "OTHER_METHOD":(total-method_counts["GET"]-method_counts["POST"]-method_counts["HEAD"])/total
    }
    return features


async def collectlogs():
    while True:
        pass
    
    
    return