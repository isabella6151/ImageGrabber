from PIL import Image
from PIL import ImageDraw
import glob
import datetime

def AddWatermark(baseImageObj, watermarkFilename):
    logoim = Image.open(watermarkFilename) #transparent image
    baseImageObj.paste(logoim, (0, baseImageObj.size[1]-logoim.size[1]), logoim)
    

def AddTimestamp(baseImageObj, datetimeObj):
    draw = ImageDraw.Draw(baseImageObj)
    draw.text((10, 10), dateTimeObj.strftime("%m/%d/%Y %I%p"), fill="yellow")
    
    
if __name__ == "__main__":
    for imageFilename in glob.glob(r"\\vmvase\D\cms\*\*\*\*.jpg"):
        print imageFilename
        
        try:
            baseImageObj = Image.open(imageFilename)
            AddWatermark(baseImageObj, "watermark.png")
            baseImageObj.save(imageFilename, "JPEG")
        except:
            continue
        
    # baseImageObj = Image.open("20110423_070007_.jpg")
    # watermarkFilename = "watermark.png"
    
    # AddWatermark(baseImageObj, watermarkFilename)
    
    # baseImageObj.save("out.png","PNG")