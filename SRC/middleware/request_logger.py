import time
from SRC.utils.logger import logger


async def log_requests(request, call_next):
    start    = time.time()
    response = await call_next(request)
    elapsed  = round((time.time() - start) * 1000, 2)
    logger.info(
        f"{request.method} {request.url.path} → {response.status_code} ({elapsed}ms)"
    )
    return response