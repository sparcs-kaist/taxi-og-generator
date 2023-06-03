from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from PIL import ImageFont, ImageDraw, Image
from io import BytesIO
import numpy as np
import requests
import cv2

app = FastAPI()
fontTitle = ImageFont.truetype("fonts/NanumSquare_acEB.ttf", 60)
fontDate = ImageFont.truetype("fonts/NanumSquare_acB.ttf", 30)
colorWhite = (255, 255, 255, 1)

def defaultImage():
    img = cv2.imread("graph.back.png")
    res, im_png = cv2.imencode(".png", img)
    return StreamingResponse(BytesIO(im_png.tobytes()), media_type="image/png")

@app.get("/{roomId}")
async def mainHandler(roomId: str = "647ac989fe1dbfb2b9408ff9"):
    try:
        # get room information
        res = requests.get("https://taxi.sparcs.org/api/rooms/publicInfo?id={}".format(roomId))
        if res.status_code != 200:
            raise ValueError("mainHandler : Invalid roomId")
        roomInfo = res.json()
        
        # load background image
        img = Image.fromarray(cv2.imread("graph.png"))
        draw = ImageDraw.Draw(img, 'RGBA')
        
        # draw Location
        draw.text((50, 50), '{} → {}'.format(roomInfo["from"]["koName"], roomInfo["to"]["koName"]), font=fontTitle, fill=colorWhite)

        # draw Date
        draw.text((50, 150), '{}'.format(roomInfo["time"]), font=fontDate, fill=colorWhite)

        # draw Name
        draw.text((50, 200), '{}'.format(roomInfo["name"]), font=fontDate, fill=colorWhite)
        
        # convert to png image
        res, img_png = cv2.imencode(".png", np.array(img))

        # response
        return StreamingResponse(BytesIO(img_png.tobytes()), media_type="image/png")
    
    except ValueError as e:
        print(e)
        return defaultImage()
    
    except Exception as e:
        print(e)
        return defaultImage()
