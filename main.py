from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from PIL import ImageFont, ImageDraw, Image
from io import BytesIO
from dotenv import load_dotenv
import datetime
import numpy as np
import requests
import cv2
import os

# load environment variables
load_dotenv()
API_ROOM_INFO = os.environ["API_ROOM_INFO"] if "API_ROOM_INFO" in os.environ \
    else "https://taxi.sparcs.org/api/rooms/publicInfo?id={}"
API_USER_INFO = os.environ["API_USER_INFO"] if "API_USER_INFO" in os.environ \
    else "https://taxi.sparcs.org/api/users/publicInfo?id={}"  # TODO: need to be updated in backend side or sync the endpoint
FRONT_URL = os.environ["FRONT_URL"] if "FRONT_URL" in os.environ \
    else "https://taxi.sparcs.org"

# KST timezone setting
timezone_kst = datetime.timezone(datetime.timedelta(hours = 9))

# initialization
app = FastAPI()
images = {
    "background": cv2.imread("images/og.background.png"),
    "background.event2023fall": cv2.imread("images/og.background.event2023fall.png"),
    "background.event2024spring": cv2.imread("images/og.background.event2024spring.png"),
    "background.event2024fall": cv2.imread("images/og.background.event2024fall.png"),
    "background.event2024fall.eventInvite": cv2.imread("images/og.background.event2024fall.eventInvite.png"),
    "default": cv2.imread("images/og.default.png"),
    "arrow.type1": cv2.imread("images/arrow.png"),
    "arrow.type2": cv2.imread("images/arrow.png"),
    "arrow.type3": cv2.imread("images/arrow.png"),
}
fonts = {
    "type1": {
        "title": ImageFont.truetype("fonts/NanumSquare_acEB.ttf", 96),
        "date": ImageFont.truetype("fonts/NanumSquare_acEB.ttf", 48),
        "name": ImageFont.truetype("fonts/NanumSquare_acR.ttf", 48),
    },
    "type2": {
        "title": ImageFont.truetype("fonts/NanumSquare_acEB.ttf", 72),
        "date": ImageFont.truetype("fonts/NanumSquare_acEB.ttf", 40),
        "name": ImageFont.truetype("fonts/NanumSquare_acR.ttf", 40), 
    },
    "type3": {
        "title": ImageFont.truetype("fonts/NanumSquare_acEB.ttf", 72),
        "date": ImageFont.truetype("fonts/NanumSquare_acEB.ttf", 40), 
        "name": ImageFont.truetype("fonts/NanumSquare_acR.ttf", 40), 
    },
}
colors = {
    "purple": (110, 54, 120, 1),
    "black": (50, 50, 50, 1),
}

def date2text(date):
    date = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(timezone_kst)
    return "{}년 {}월 {}일 {}요일 {} {}".format(
        date.year,
        date.month,
        date.day,
        ["월", "화", "수", "목", "금", "토", "일"][date.weekday()],
        "오전" if date.strftime("%p") == "AM" else "오후",
        date.strftime("%-I:%M"),
    )

def predictWidth(draw, text, font):
    width, _ = draw.textsize(text, font=font)
    return width

def defaultImage():
    _, im_png = cv2.imencode(".png", images["default"])
    return StreamingResponse(BytesIO(im_png.tobytes()), media_type="image/png")

@app.get("/{roomId}")
async def mainHandler(roomId: str):
    try:
        # if roomId ends with .png, remove it
        if roomId.endswith(".png"): roomId = roomId[:-4]
        
        # get room information
        res = requests.get(API_ROOM_INFO.format(roomId), headers={"Origin": FRONT_URL})
        if res.status_code != 200:
            raise ValueError("mainHandler : Invalid roomId")
        roomInfo = res.json()

        # convert room information to text
        text = {
            "from": roomInfo["from"]["koName"],
            "to": roomInfo["to"]["koName"],
            "date": date2text(roomInfo["time"]),
            "name": roomInfo["name"],
        }

        event_type = "event2024fall"    #back to None
        
        # load background image
        img_og = Image.fromarray(images["background"] if event_type == None else images["background.{}".format(event_type)])
        draw = ImageDraw.Draw(img_og, 'RGBA')

        # select draw type
        # if location text width is less than 784, use type1
        # else, use type2
        draw_type = "type1" if predictWidth(draw, text["from"] + text["to"], fonts["type1"]["title"]) <= 784 \
            else "type2" if predictWidth(draw, text["from"] + text["to"], fonts["type2"]["title"]) <= 784 \
            else "type3"
        
        if event_type == "event2024fall" and draw_type == "type1":  
            draw_type = "type2"
        
        # draw location
        draw.text((52, 52), text["from"], font=fonts[draw_type]["title"], fill=colors["purple"])
        widthFrom = predictWidth(draw, text["from"], fonts[draw_type]["title"])
        draw.text(
            (52 + 20 + 96 + widthFrom, 52) if draw_type == "type1" or draw_type == "type2" else (172, 166),
            text["to"],
            font=fonts[draw_type]["title"],
            fill=colors["purple"]
        )

        # draw arrow
        img_arrow = Image.fromarray(images["arrow.{}".format(draw_type)]).convert('RGBA')
        img_og.paste(
            img_arrow,
            (52 + 10 + widthFrom, 52) if draw_type == "type1" \
                else (52 + 10 + widthFrom, 52 - 7) if draw_type == "type2" \
                else (52, 160)
        )

        # draw date
        draw.text(
            (52, 189) if draw_type == "type1" \
                else (52, 150) if draw_type == "type2" \
                else (52, 280),
            text["date"],
            font=fonts[draw_type]["date"],
            fill=colors["black"]
        )

        # ellipsis if name has long width
        if predictWidth(draw, text["name"], fonts[draw_type]["name"]) > 450: # back to 700
            while predictWidth(draw, text["name"] + "...", fonts[draw_type]["name"]) > 450: # back to 700
                text["name"] = text["name"][:-1]
            text["name"] += "..."
        
        # draw name
        draw.text((52, 392) if draw_type == "type1" else (52, 401), 
            text["name"],
            font=fonts[draw_type]["name"],
            fill=colors["black"]
        )
        
        # convert to png image
        res, img_png = cv2.imencode(".png", np.array(img_og))

        # response
        return StreamingResponse(BytesIO(img_png.tobytes()), media_type="image/png")
    
    except ValueError as e:
        print(e)
        return defaultImage()
    
    except Exception as e:
        print(e)
        return defaultImage()

    @app.get("/eventInvite/{userId}")
    async def eventInviteHandler(userId: str):
        try:
            # get user information
            res = requests.get(API_USER_INFO.format(userId), headers={"Origin": FRONT_URL})
            if res.status_code != 200:
                raise ValueError("recommandHandler : Invalid userId")
            userInfo = res.json()

            # convert user information to text
            text = {
                "nickname": userInfo["nickname"],
                "profileImageUrl": userInfo["profileImageUrl"],
            }

            event_type = "event2024fall.eventInvite"    

            # load background image
            img_og = Image.fromarray(images["background"] if event_type == None else images["background.{}".format(event_type)])
            draw = ImageDraw.Draw(img_og, 'RGBA')

            # select draw type
            # if location text width is less than 784, use type1
            # else, use type2
            draw_type = "type1" if predictWidth(draw, text["from"] + text["to"], fonts["type1"]["title"]) <= 784 \
                else "type2" if predictWidth(draw, text["from"] + text["to"], fonts["type2"]["title"]) <= 784 \
                else "type3"
            
            if event_type == "event2024fall.eventInvite" and draw_type == "type1":  
                draw_type = "type2"

            # draw nickname

            # draw profile image

        except ValueError as e: 
            print(e)
            return defaultImage()