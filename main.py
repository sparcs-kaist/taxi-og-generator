from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from PIL import ImageFont, ImageDraw, Image
from io import BytesIO
import numpy as np
import cv2

app = FastAPI()
fontTitle = ImageFont.truetype("fonts/NanumGothic-ExtraBold.ttf", 60)
fontDate = ImageFont.truetype("fonts/NanumGothic-Bold.ttf", 30)

@app.get("/")
async def mainHandler(from_name: str = "", to_name: str = ""):
    color = (255, 255, 255, 1)

    # load image
    img = Image.fromarray(cv2.imread("graph.png"))
    
    # draw text
    draw = ImageDraw.Draw(img, 'RGBA')
    draw.text((100, 100), '{} → {}'.format(from_name, to_name), font=fontTitle, fill=color)
    draw.text((100, 200), '2023년 6월 4일 일요일 오후 9:00', font=fontDate, fill=color)
    
    # convert to png image
    res, img_png = cv2.imencode(".png", np.array(img))

    # response
    return StreamingResponse(BytesIO(img_png.tobytes()), media_type="image/png")
