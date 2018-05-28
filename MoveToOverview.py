import os
import os.path
import shutil

for camDir in os.listdir("."):
    if os.path.isdir(camDir):
        print camDir
        for imageFilename in os.listdir(camDir):
            fullFilePath = r"%s\%s" % (camDir, imageFilename)
            if os.path.isfile(fullFilePath) and os.path.basename(imageFilename) != "Thumbs.db":
                shutil.move(fullFilePath, r"%s\overview\%s" % (camDir, imageFilename))