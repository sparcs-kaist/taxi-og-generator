from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from io import BytesIO
import cv2

app = FastAPI()

@app.get("/")
async def mainHandler(from_name: str = "", to_name: str = ""):
    img = cv2.imread("graph.png")
    res, im_png = cv2.imencode(".png", img)
    return StreamingResponse(BytesIO(im_png.tobytes()), media_type="image/png")
