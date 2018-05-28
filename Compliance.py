import urllib2
import sys
import os
import os.path
import datetime
import ftplib
import time
import base64
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import math
import pdb
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
import smtplib
import atexit
from win32com.client import GetObject

class FtpConnection:
    def __init__(self, optsFileDict):
        ftp = ftplib.FTP(optsFileDict["ftpServer"])
        ftp.login(optsFileDict["ftpUsername"], optsFileDict["ftpPassword"])
        try:
            ftp.cwd(optsFileDict["ftpDir"])
        except ftplib.error_perm,e:
            dirName = optsFileDict["ftpDir"]
            print "\tCreating dir %s"%dirName
            ftp.mkd(dirName)
            ftp.cwd(dirName)

        self.ftp = ftp
        
        
    def UploadImages(self, filenameList):
        errorMsgList = []
        rmImages = []
        currCam = ''
        num = 0
        countByCam = {}
        for filename in filenameList:
            cam = filename.split('\\')[2]
            try:
                countByCam[cam] += 1
            except KeyError:
                countByCam[cam] = 0
        print "Details of images to be sent:"
        for cam, count in countByCam.iteritems():
            print "%s: %d"%(cam,count)
        for filename in filenameList:
            cam = filename.split('\\')[2]
            if cam != currCam or len(rmImages) > 20:
                currCam = cam
                for fname in rmImages:
                    try:
                        os.remove(fname)
                    except WindowsError,e:
                        if e[0] == 32:
                            pass
                        else:
                            raise
                rmImages = []
            presetDir = os.path.basename(os.path.dirname(filename))
            camDir = os.path.basename(os.path.dirname(os.path.dirname(filename)))
            date_month = os.path.basename(filename).split('_')[0]
            time_hour =  os.path.basename(filename).split('_')[1]
            year = date_month[:4]
            month = date_month[4:6]
            target = os.sep.join([camDir, presetDir,year, month])
            storCommand = r"STOR %s\%s" % (target, os.path.basename(filename))
            success = 0
            # print storCommand
            try:
                self.ftp.storbinary(storCommand, open(filename, "rb"))
                num+=1
                print "Sent %s: %s\t%s\t(%d/%d)"%(currCam, date_month, time_hour,num,countByCam[currCam])
                success = 1
            except ftplib.error_perm,e:
                print "\tCreating dir %s"%target
                self.ftp.mkd(target)
                self.ftp.storbinary(storCommand, open(filename, "rb"))
                success = 1
            except ftplib.all_errors, e:
                print "\t-->%s was not STOR'ed"%os.path.basename(filename)
                print e
                errorMsg = '%s\n'%filename
                errorMsg += '%s\n'%e.args[0]
                errorMsg += '----------------------------------------\n\n'
                errorMsgList.append(errorMsg)                
            if success:
                remoteSz = self.ftp.size(os.sep.join([target,os.path.basename(filename)]))
                localSz = os.path.getsize(filename)
                if math.floor(abs(remoteSz-localSz)) == 0.0:
                    rmImages.append(filename)

        # [os.remove(fname) for fname in rmImages]
        for fname in rmImages:
            try:
                os.remove(fname)
            except WindowsError,e:
                if e[0] == 32:
                    pass
                else:
                    raise        
        return errorMsgList
    
    def __del__(self):
        self.ftp.quit()

class StatusMsg:
    def __init__(self, text):
        self.msg = text

class Camera:
    def __init__(self, name, ip, rotation, defaultOutDir):
        self.name = name
        self.ip = ip
        self.defaultOutDir = defaultOutDir
        self.rotation = float(rotation)
        
    def AddWatermark(self, baseImageObj, watermarkFilename):
        logoim = Image.open(watermarkFilename)
        baseImageObj.paste(logoim, (0, baseImageObj.size[1]-logoim.size[1]), logoim)
        
        
    def GetTimestamp(self, datetimeObj):
        timestamp = datetimeObj.strftime("%a. %b %d, %Y ") + str(int(datetimeObj.strftime("%I"))) + datetimeObj.strftime(":%M%p")
        return timestamp
        
        
    def AddTimestamp(self, baseImageObj, datetimeObj):
        draw = ImageDraw.Draw(baseImageObj)
        font = ImageFont.truetype(r"C:\WINDOWS\Fonts\arial.ttf", 18)
        
        timestamp = self.GetTimestamp(datetimeObj)
        textWidth, textHeight = draw.textsize(timestamp, font=font)
        
        xCoord = baseImageObj.size[0] - textWidth - 5
        yCoord = baseImageObj.size[1] - textHeight
        
        draw.text((xCoord, yCoord), timestamp, fill="white", font=font)
        
     
    def FetchImage(self, outDir = None, presetName = "overview"):
        print "Fetching", self.name, presetName
        if not outDir:
            outDir = self.defaultOutDir
            
        url = "http://%s/axis-cgi/jpg/image.cgi?resolution=640x480" % self.ip
        camOutDir = r"%s\%s\%s" % (outDir, self.name, presetName)

        try:
            os.makedirs(camOutDir)
        except:
            pass

        currentTime = datetime.datetime.now()
        outFilename = r"%s\%s.jpg" % (camOutDir, currentTime.strftime("%Y%m%d_%H%M%S_%f"))

        # go to preset view
        try:
            if presetName != "overview":
                self.GoToPtzPreset(presetName)
        except ValueError:
            print "Invalid preset: %s" % presetName
            msg = StatusMsg("Invalid preset: %s for cam: %s with ip: %s" %(presetName, self.name, self.ip))
            return msg
            
        encodedstring = base64.encodestring("%s:%s" % (optsFileDict["camUsername"], optsFileDict["camPassword"])) 
        encodedstring = encodedstring.replace("\n","")       
        authString = "Basic %s" % encodedstring
        request = urllib2.Request(url, None, {"Authorization":authString})
        try:
            pageHandle = urllib2.urlopen(request)
        except:
            print "\tCannot connect to %s"%self.name
            msg = StatusMsg("Cannot connect to cam: %s with ip: %s" %(self.name, self.ip))
            return msg
        open(outFilename, 'wb').write(pageHandle.read())

        with open(outFilename,'rb') as fptr:
            img = Image.open(fptr)
            # rotate image
            if self.rotation:
                img.rotate(self.rotation)
            # add watermark and timestamp
            self.AddWatermark(img, "watermark.png")
            self.AddTimestamp(img, currentTime)
            img.save(outFilename)
            del img

            if presetName != "overview":
                self.GoToPtzPreset("overview")

        return outFilename
            
    def GoToPtzPreset(self, presetName):
        url = "http://%s/axis-cgi/com/ptz.cgi?gotoserverpresetname=%s" % (self.ip, presetName)
        pageContent = urllib.urlopen(url).read()
        if "No such preset position found" in pageContent:
            raise ValueError
        time.sleep(2)
        
    def ZoomOut(self):
        url = "http://%s/axis-cgi/com/ptz.cgi?zoom=1" % self.ip
        urllib.urlopen(url)
        
        
    def ZoomIn(self, zoomParam):
        url = "http://%s/axis-cgi/com/ptz.cgi?zoom=%d" % (self.ip, zoomParam)
        urllib.urlopen(url)


def ParseOptsFile(optsFilename):
    optsFileDict = {}

    inFile = open(optsFilename)
    for line in inFile:
        key, value = line.split(":-")
        optsFileDict[key] = value.strip()

    return optsFileDict


def InitCamList(optsFileDict):
    camList = []
    
    defaultOutDir = optsFileDict["outDir"]
    specialKeys = ["outDir", "camUsername", "camPassword", "ftpServer", "ftpUsername", "ftpPassword", "ftpDir","siteId","toList","mailServer"]
    # keyList = [key for key in optsFileDict.keys() if key not in specialKeys]
    keyList = [key for key in optsFileDict.keys() if\
        ('cam' in key.lower() or 'zoom' in key.lower() or 'fac' in key.lower()) and key not in specialKeys]
    for key in keyList:
        name = key
        try:
            ip, rotation = optsFileDict[key].split(",")
        except:
            ip, rotation = optsFileDict[key], 0
        cam = Camera(name, ip, rotation, defaultOutDir)
        camList.append(cam)
    
    return camList
    
    
def FetchImages(camList, presetList):
    outFilenameList = []
    errorMsgList = []
    for presetName in presetList:
        for cam in camList:
            retVal = cam.FetchImage(presetName = presetName)
            if isinstance(retVal,str):
                outFilenameList.append(retVal)
            else:
                msg = retVal.msg + "\n-------------------------------------------------------------\n\n"
                errorMsgList.append(msg)
    return outFilenameList, errorMsgList


class CMSEmail:
    def __init__(self):
        self.msg = MIMEMultipart()
    def __setFrom(self):
        self.me = "noreply@videomining.com"
        self.msg['From'] = self.me
    def __setToList(self,toList):
        self.you = toList
        commaspace = '; '
        self.msg['To'] = commaspace.join(toList)
    def __setAttachments(self,attachments):
        for fileName in attachments:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(open(fileName, 'rb').read())
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                   'attachment; filename="%s"' % os.path.basename(fileName))
            self.msg.attach(part)
    def __setSubject(self,subject):
        self.msg['Subject'] = subject
    def __setText(self,text):
        self.msg.attach(MIMEText(text))
    def __setServer(self,server):
        try:
            self.server = smtplib.SMTP(server)
        except Exception,e:
            print e
        else:
            self.server.set_debuglevel(True)
        username = 'VIDEOMINING\dhari'
        password = 'bcv5d5sa'
        try:
            # self.server.login('dhari@videomining.com','bcv5d5sa')
            self.server.login(username,password)
        except smtplib.SMTPAuthenticationError, e:
            # if login fails, try again using a manual plain login method
            self.server.docmd("AUTH LOGIN", base64.b64encode( username ))
            self.server.docmd(base64.b64encode( password ), "")
        
    def __sendEmail(self):
        try:
            self.server.sendmail(self.me, self.you, self.msg.as_string())
        except smtplib.SMTPRecipientsRefused, errorObj:
            print errorObj.recipients
    def sendEmail(self,server='',attachment=[],toList=[],subject='',text=''):
        pdb.set_trace()
        self.__setFrom()
        toList = toList.split(";")
        self.__setToList(toList)
        self.__setAttachments(attachment)
        self.__setSubject(subject)
        self.__setText(text)
        self.__setServer(server)        
        self.__sendEmail()
    def __del__(self):
        if self.server:
            self.server.quit()


    
    
def emailFTPErrors(optsfileDict, ftpErrorList):
    ftpeml = CMSEmail()
    errorMsgStr = ''
    for errorMsg in ftpErrorList:
        errorMsgStr += (errorMsg + "\n\n")
    ftpeml.sendEmail(optsfileDict['mailServer'],[],optsfileDict['toList'],'FTP errors from %s'%(optsfileDict['siteId']),errorMsgStr)
    
    
def getTime():
    import datetime
    now = datetime.datetime.now()
    name = now.strftime("%Y_%m_%d_%H_%M_%S")
    return name

def getLogFileName(opt=''):
    name = getTime()
    name = name + '_' + opt
    name = name.rstrip('_')
    return name + '.log'

def saveErrors(errorList, fName):
    if len(errorList) == 0:
        return
    fp = open(fName,'w')
    for errorMsg in errorList:
        fp.write(errorMsg)
    fp.close()
def __getCurrPids():
    
    WMI = GetObject('winmgmts:')
    processes = WMI.InstancesOf('Win32_Process')
    return [process.Properties_('ProcessID').Value for process in processes]

def __FTPTransferStatus(dir):
    '''
    every time the script starts up it checks the presence of a lock file that stores the pid of the process that ran the script
    the last time (that process could very well  be still running). If the process exit normally, the lock file is removed. If
    the lock file is present it means one of two things - the process is still running or it quit with an error. If the process
    is still running, return FALSE. If the process isn't running it implies that the process that created the file quit without
    a cleanup further implying that it is okay for the current process to overwrite the lock file and proceed
    '''
    file = dir + os.sep + "lockfile.lock"
    curr_pid = os.getpid()

    if os.path.exists(file):
            #if the lockfile is already there then check the PID number in the lock file
            pidfile = open(file, "r")
            pidfile.seek(0)
            old_pid = pidfile.readline()
            # curr_pid = os.getpid()
            if int(old_pid) in __getCurrPids():
                    print "The previous instance is still running: process %s\nCurrent process %s will exit without FTP"%(old_pid,curr_pid)
                    return False
            else:
                # this means that the previous process exiting abnormally still leaving behind the lock file
                pidfile = open(file, "w")
                pidfile.write("%s" % curr_pid)
                pidfile.close()
                return True
    else:
        pidfile = open(file, "w")
        pidfile.write("%s" % curr_pid)
        pidfile.close()
        return True
        

def __removeLock(dir):
    file = dir + os.sep + 'lockfile.lock'
    
    if os.path.exists(file):
        os.remove(dir + os.sep + 'lockfile.lock')
        
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Usage: FetchImages.py <optsFile> <overview|endcaps|all>"
        sys.exit()
    
    optsFilename = sys.argv[1]
    optsFileDict = ParseOptsFile(optsFilename)
    
    
    mode = sys.argv[2]
    if mode == "overview":
        presetList = ["overview"]
    elif mode == "endcaps":
        presetList = ["endcap1", "endcap2"]
    elif mode == "all":
        presetList = ["overview", "endcap1", "endcap2"]
    else:
        raise ValueError("Invalid mode: %s" % sys.argv[2])


    camList = InitCamList(optsFileDict)   
    outFilenameList = []
    errorMsgList = []
    outFilenameList, errorMsgList = FetchImages(camList, presetList)
    # check if another instance of the script is running. If so, exit else continue with FTP transfer
    flag = __FTPTransferStatus(optsFileDict['outDir'])
    if not flag:
        sys.exit()
    # remove the lock file when current script exits normally
    atexit.register(__removeLock,optsFileDict['outDir'])    
    
    platformHome = optsFileDict['outDir']    
    listOfFtpErrors = []
    if errorMsgList != []:
        print "\n\nFetch Errors\n"
        print "----------------"
        for errorMsg in errorMsgList:
            print errorMsg    
    # send out the latest snapshots
    if outFilenameList != []:
        ftp = FtpConnection(optsFileDict)
        ftpErrorList = ftp.UploadImages(outFilenameList)
        if ftpErrorList != []:
            print "\n\nFTP Errors\n"
            print "----------------"
            for errorMsg in ftpErrorList:
                print errorMsg  
            listOfFtpErrors.extend(ftpErrorList)
    else:
        print "\n\nNo camera images were fetched -OR- were present for FTP. Skipping upload\n\n"            
            
    # sniff the other folders for images left over from previous runs and attempt to FTP them over
    ftp = FtpConnection(optsFileDict)
    for dir, subdirs, filenames in os.walk(platformHome):
        if dir == platformHome or subdirs != []:
            continue
        ftpList = []
        str = dir[len(platformHome+"\\"):]
        camNum = str.split('\\')[0]
        viewDesc = str.split('\\')[-1]
        print "%s --> %s"%(camNum, viewDesc)
        filenames = [f for f in filenames if f.split('.')[-1] == 'jpg']
        filenames = [dir + os.sep + f for f in filenames]
        fileSet = set(filenames).difference(outFilenameList)
        if len(fileSet) == 0:
            print "\tNO FILES"
            continue
        ftpList.extend(list(fileSet))
        if ftpList != []:
            print "\tsending %d images"%len(ftpList)
            ftpErrorList = ftp.UploadImages(ftpList)
            if ftpErrorList != []:
                print "\n\nFTP Errors\n"
                print "----------------"
                for errorMsg in ftpErrorList:
                    print errorMsg
                listOfFtpErrors.extend(ftpErrorList)
        else:
            print "\n\nNo camera images were fetched -OR- were present for FTP. Skipping upload\n\n"        

        
    # email ftp reports and errors connecting to cameras separately
    # emailFTPErrors(optsFileDict, ftpErrorList)
    fName = platformHome + os.sep + getLogFileName('FTPErrors')
    saveErrors(listOfFtpErrors, fName)
    fName = platformHome + os.sep + getLogFileName('CamConnectionErrors')
    saveErrors(errorMsgList, fName)
    
