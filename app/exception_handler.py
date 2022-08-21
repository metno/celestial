import logging
from fastapi.responses import JSONResponse

headers = {"Access-Control-Allow-Origin": "*",
           "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS, HEAD",
           "Access-Control-Allow-Headers": "X-Requested-With, access-control-allow-origin, Content-Type, Accept, authorization"}


async def http_exception_handler(request, exc):
    """
    This function handles exceptions raised by the application
    of the type HTTPException imported from the fastapi library
    """
    logging.exception(f"Call to endpoint {request.url.path} "
                      f"failed with status_code {exc.status_code}")
    return(JSONResponse(str(exc.detail),
                        headers=headers,
                        status_code=exc.status_code))