from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import glob
import datetime
import os.path

def AddWatermark(baseImageObj, watermarkFilename):
    logoim = Image.open(watermarkFilename) #transparent image
    baseImageObj.paste(logoim, (0, baseImageObj.size[1]-logoim.size[1]), logoim)
    

def GetTimestamp(datetimeObj):
    timestamp = datetimeObj.strftime("%a. %b %d, %Y ") + datetimeObj.strftime("%I").replace("0", "") + datetimeObj.strftime(":%M%p")
    return timestamp
    
    
def AddTimestamp(baseImageObj, datetimeObj):
    draw = ImageDraw.Draw(baseImageObj)
    font = ImageFont.truetype("arial.ttf", 18)
    
    timestamp = GetTimestamp(datetimeObj)
    textWidth, textHeight = draw.textsize(timestamp, font=font)
    
    xCoord = baseImageObj.size[0] - textWidth - 5
    yCoord = baseImageObj.size[1] - textHeight
    
    draw.text((xCoord, yCoord), timestamp, fill="white", font=font)
    
    
if __name__ == "__main__":
    for imageFilename in glob.glob(r"\\vmvase\D\cms\swy2607\*\*\*.jpg"):
    # for imageFilename in glob.glob(r"cam001\overview\*.jpg"):
        print imageFilename
        datetimeObj = datetime.datetime.strptime(os.path.basename(imageFilename), "%Y%m%d_%H%M%S_.jpg")
        
        if datetimeObj >= datetime.datetime(2011, 6, 1, hour = 11, minute = 15):
            continue
        
        try:
            baseImageObj = Image.open(imageFilename)
            AddTimestamp(baseImageObj, datetimeObj)
            baseImageObj.save(imageFilename, "JPEG")
        except:
            continue

    # baseImageObj = Image.open("20110307_152549_.jpg")
    # watermarkFilename = "watermark_smaller.png"
    
    # AddWatermark(baseImageObj, watermarkFilename)
    # AddTimestamp(baseImageObj, datetime.datetime.now())
    
    # baseImageObj.save("out_vertical.png","PNG")
    
    
    # baseImageObj = Image.open("20110423_070007_.jpg")
    # watermarkFilename = "watermark_smaller.png"
    
    # AddWatermark(baseImageObj, watermarkFilename)
    # AddTimestamp(baseImageObj, datetime.datetime.now())
    
    # baseImageObj.save("out_horizontal.png","PNG")
    
    