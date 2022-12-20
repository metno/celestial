import logging
from http import HTTPStatus
from fastapi.responses import JSONResponse

headers = {"Access-Control-Allow-Origin": "*",
           "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS, HEAD",
           "Access-Control-Allow-Headers": "X-Requested-With, access-control-allow-origin, Content-Type, Accept, authorization"}


async def http_exception_handler(request, exc):
    """
    This function handles exceptions raised by the application
    of the type HTTPException imported from the fastapi library
    """
    logging.info(f"Call to endpoint {request.url.path} "
                 f"failed with status_code {exc.status_code}")
    return(JSONResponse(str(exc.detail),
                        headers=headers,
                        status_code=exc.status_code))

async def unexpected_exception_handler(request, exc):
    logging.info(f"Call to endpoint {request.url.path} "
                 f"failed with status_code {exc.status_code}. "
                 f"Error message: {str(exc.detail)}")
    return(JSONResponse(f"Call to endpoint {request.url.path} failed with an "
                        "unexpected exception",
                        headers=headers,
                        status_code=HTTPStatus.INTERNAL_SERVER_ERROR))