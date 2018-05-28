import Compliance
import glob
import sys

if __name__ == "__main__":
    globString = sys.argv[1]
    optsFileDict = Compliance.ParseOptsFile("optsFile.txt")
    ftp = Compliance.FtpConnection(optsFileDict)
    filenameList = glob.glob(globString)
    ftp.UploadImages(filenameList)