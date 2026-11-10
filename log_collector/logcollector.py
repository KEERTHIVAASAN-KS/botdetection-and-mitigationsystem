import asyncio
import json
import aiofiles
import httpx

LOG_FILE = "/var/log/nginx/bot_access.log"
HTTP_ENDPOINT = "http://127.0.0.1:8000/http"

SEND_INTERVAL = 5
READ_INTERVAL = 0.1

IGNORED_PATHS = {
    "/http", "/mouse", "/fingerprint",
    "/nginxenforcement", "/check_access"
}


# Calculate cumulative HTTP features
def calculatehttpfeatures(s):

    total = s["count"]

    if total == 0:
        return None

    totalduration = s["last"] - s["first"]

    avgtime = totalduration / (total - 1) if total > 1 else 0

    features = {
        "NUMBER_OF_REQUESTS": total,
        "TOTAL_DURATION": totalduration,
        "AVERAGE_TIME": avgtime,
        "REPEATED_REQUESTS": s["repeated"] / total,

        "HTTP_RESPONSE_2XX": s["status"][2] / total,
        "HTTP_RESPONSE_3XX": s["status"][3] / total,
        "HTTP_RESPONSE_4XX": s["status"][4] / total,
        "HTTP_RESPONSE_5XX": s["status"][5] / total,

        "GET_METHOD": s["methods"]["GET"] / total,
        "POST_METHOD": s["methods"]["POST"] / total,
        "HEAD_METHOD": s["methods"]["HEAD"] / total,

        "OTHER_METHOD": (
            total - s["methods"]["GET"]
            - s["methods"]["POST"]
            - s["methods"]["HEAD"]
        ) / total
    }

    return features


# Log collector
async def collectlogs():

    sessions = {}
    updated_sessions = set()

    async with aiofiles.open(LOG_FILE, mode="r") as logfile:

        await logfile.seek(0, 2)

        async with httpx.AsyncClient(timeout=10) as client:

            loop = asyncio.get_running_loop()
            last_send = loop.time()

            while True:

                # Read new log entries
                while True:

                    line = await logfile.readline()

                    if not line:
                        break

                    try:
                        r = json.loads(line)

                        sid = r["session_id"]
                        path = r["path"]
                        method = r["method"].upper()
                        status = int(r["status_code"])
                        timestamp = float(r["timestamp"])

                        if not sid or path in IGNORED_PATHS:
                            continue

                        # Create session if it does not exist
                        if sid not in sessions:
                            sessions[sid] = {
                                "count": 0,
                                "first": timestamp,
                                "last": timestamp,
                                "repeated": 0,
                                "seen": set(),
                                "status": {2: 0, 3: 0, 4: 0, 5: 0},
                                "methods": {
                                    "GET": 0,
                                    "POST": 0,
                                    "HEAD": 0
                                },
                                "features": None
                            }

                        s = sessions[sid]

                        # Update cumulative values
                        s["count"] += 1
                        s["first"] = min(s["first"], timestamp)
                        s["last"] = max(s["last"], timestamp)

                        path_method = (path, method)

                        if path_method in s["seen"]:
                            s["repeated"] += 1

                        s["seen"].add(path_method)

                        status_class = status // 100

                        if status_class in s["status"]:
                            s["status"][status_class] += 1

                        if method in s["methods"]:
                            s["methods"][method] += 1

                        # Calculate latest features
                        s["features"] = calculatehttpfeatures(s)

                        updated_sessions.add(sid)

                    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
                        continue

                # Send updated session features every 5 seconds
                if loop.time() - last_send >= SEND_INTERVAL:

                    for sid in list(updated_sessions):

                        features = sessions[sid]["features"]

                        try:
                            response = await client.post(
                                HTTP_ENDPOINT,
                                json={
                                    "sessionid": sid,
                                    "features": features
                                }
                            )

                            response.raise_for_status()

                            updated_sessions.discard(sid)

                        except httpx.HTTPError as e:
                            print(f"HTTP sending error for {sid}: {e}")

                    last_send = loop.time()

                await asyncio.sleep(READ_INTERVAL)