# IMPORT
print 'Importing SiSo Wrapper'
try:
    import SiSoPyInterface as s
except ImportError:
    raise ImportError('SiSo module not loaded successfully')

print 'Runtime Version', s.Fg_getSWVersion()
from matplotlib import pyplot as plt
from skimage.io import imsave
# IMPORT additional modules
import sys
import time
import cv2
from realtime_eyetracker import *

# for "s.getArrayFrom", to handle grabbed image as NumPy array
# print 'Importing NumPy',
import numpy as np

# print 'Version', np.__version__


# DEFINITIONS

# returns count of available boards
def getNrOfBoards():
    nrOfBoards = 0
    (err, buffer, buflen) = s.Fg_getSystemInformation(None, s.INFO_NR_OF_BOARDS, s.PROP_ID_VALUE, 0)
    if (err == s.FG_OK):
        nrOfBoards = int(buffer)
    return nrOfBoards


# Lets the user select one of the available boards, returns the selected board, or -1 if nothing is selected
def selectBoardDialog():
    maxNrOfboards = 10
    nrOfBoardsFound = 0
    nrOfBoardsPresent = getNrOfBoards()
    maxBoardIndex = -1
    minBoardIndex = None

    if (nrOfBoardsPresent <= 0):
        print "No Boards found!"
        return -1

    print
    print 'Found', nrOfBoardsPresent, 'Board(s)'

    for i in range(0, maxNrOfboards):
        skipIndex = False
        boardType = s.Fg_getBoardType(i);
        if boardType == s.PN_MICROENABLE4AS1CL:
            boardName = "MicroEnable IV AS1-CL"
        elif boardType == s.PN_MICROENABLE4AD1CL:
            boardName = "MicroEnable IV AD1-CL"
        elif boardType == s.PN_MICROENABLE4VD1CL:
            boardName = "MicroEnable IV VD1-CL"
        elif boardType == s.PN_MICROENABLE4AD4CL:
            boardName = "MicroEnable IV AD4-CL"
        elif boardType == s.PN_MICROENABLE4VD4CL:
            boardName = "MicroEnable IV VD4-CL"
        elif boardType == s.PN_MICROENABLE4AQ4GE:
            boardName = "MicroEnable IV AQ4-GE"
        elif boardType == s.PN_MICROENABLE4VQ4GE:
            boardName = "MicroEnable IV VQ4-GE"
        elif boardType == s.PN_MICROENABLE5AQ8CXP6B:
            boardName = "MicroEnable V AQ8-CXP"
        elif boardType == s.PN_MICROENABLE5VQ8CXP6B:
            boardName = "MicroEnable V VQ8-CXP"
        elif boardType == s.PN_MICROENABLE5VD8CL:
            boardName = "MicroEnable 5 VD8-CL"
        elif boardType == s.PN_MICROENABLE5AD8CL:
            boardName = "MicroEnable 5 AD8-CL"
        elif boardType == s.PN_MICROENABLE5AQ8CXP6D:
            boardName = "MicroEnable 5 AQ8-CXP6D"
        elif boardType == s.PN_MICROENABLE5VQ8CXP6D:
            boardName = "MicroEnable 5 VQ8-CXP6D"
        elif boardType == s.PN_MICROENABLE5AD8CLHSF2:
            boardName = "MicroEnable 5 AD8-CLHS-F2"
        elif boardType == s.PN_MICROENABLE5_LIGHTBRIDGE_ACL:
            boardName = "MicroEnable 5 LB-ACL"
        elif boardType == s.PN_MICROENABLE5_LIGHTBRIDGE_VCL:
            boardName = "MicroEnable 5 LB-VCL"
        elif boardType == s.PN_MICROENABLE5_MARATHON_ACL:
            boardName = "MicroEnable 5 MA-ACL"
        elif boardType == s.PN_MICROENABLE5_MARATHON_ACX_SP:
            boardName = "MicroEnable 5 MA-ACX-SP"
        elif boardType == s.PN_MICROENABLE5_MARATHON_ACX_DP:
            boardName = "MicroEnable 5 MA-ACX-DP"
        elif boardType == s.PN_MICROENABLE5_MARATHON_ACX_QP:
            boardName = "MicroEnable 5 MA-ACX-QP"
        elif boardType == s.PN_MICROENABLE5_MARATHON_AF2_DP:
            boardName = "MicroEnable 5 MA-AF2-DP"
        elif boardType == s.PN_MICROENABLE5_MARATHON_VCL:
            boardName = "MicroEnable 5 MA-VCL"
        elif boardType == s.PN_MICROENABLE5_MARATHON_VCX_QP:
            boardName = "MicroEnable 5 MA-VCX-QP"
        elif boardType == s.PN_MICROENABLE5_MARATHON_VF2_DP:
            boardName = "MicroEnable 5 MA-VF2-DP"
        else:
            boardName = "Unknown / Unsupported Board"
            skipIndex = True

        if not skipIndex:
            sys.stdout.write("Board ID " + str(i) + ": " + boardName + " 0x" + format(boardType, '02X') + "\n")
            nrOfBoardsFound = nrOfBoardsFound + 1
            maxBoardIndex = i
            if minBoardIndex == None: minBoardIndex = i

        if nrOfBoardsFound >= nrOfBoardsPresent:
            break

        if nrOfBoardsFound < 0:
            break

    if nrOfBoardsFound <= 0:
        out("No Boards found!")
        return -1

    inStr = "=====================================\n\nPlease choose a board[{0}-{1}]: ".format(minBoardIndex,
                                                                                               maxBoardIndex)
    userInput = input(inStr)

    while userInput > maxBoardIndex or userInput < minBoardIndex:
        inStr = "Invalid selection, retry[{0}-{1}]: ".format(minBoardIndex, maxBoardIndex)
        userInput = input(inStr)

    return userInput


# MAIN
def adjust_threshold(width=544,height=500,threshold=200, kernel=5, xy=[30,160,235,320]):
    # Board and applet selection
    boardId = 0

    if boardId < 0:
        exit(1)

    # definition of resolution
    samplePerPixel = 1
    bytePerSample = 1
    isSlave = False
    useCameraSimulator = False
    camPort = s.PORT_A

    # number of buffers for acquisition
    nbBuffers = 8
    totalBufferSize = width * height * samplePerPixel * bytePerSample * nbBuffers

    # number of image to acquire
    nrOfPicturesToGrab = s.GRAB_INFINITE


    # Get Loaded Applet
    boardType = s.Fg_getBoardType(boardId)
    if boardType == s.PN_MICROENABLE4AS1CL:
        applet = "SingleAreaGray16"
    elif boardType == s.PN_MICROENABLE4AD1CL or boardType == s.PN_MICROENABLE4AD4CL or boardType == s.PN_MICROENABLE4VD1CL or boardType == s.PN_MICROENABLE4VD4CL:
        applet = "DualAreaGray16"
    elif boardType == s.PN_MICROENABLE4AQ4GE or boardType == s.PN_MICROENABLE4VQ4GE:
        applet = "QuadAreaGray16";
    else:
        (err, applet) = s.Fg_findApplet(boardId)
        if err != 0:
            print "No applet is found"
            exit(0)
        else:
            print 'Applet found:', applet

    # INIT FRAMEGRABBER

    print 'Initializing Board ..',

    if isSlave:
        fg = s.Fg_InitEx(applet, boardId, 1);
    else:
        fg = s.Fg_InitEx(applet, boardId, 0);

    # error handling
    err = s.Fg_getLastErrorNumber(fg)
    mes = s.Fg_getErrorDescription(err)

    if err < 0:
        print "Error", err, ":", mes
        sys.exit()
    else:
        print "ok"

    # allocating memory
    memHandle = s.Fg_AllocMemEx(fg, totalBufferSize, nbBuffers)

    # Set Applet Parameters
    err = s.Fg_setParameterWithInt(fg, s.FG_FORMAT,s.FG_GRAY, camPort)
    err = s.Fg_setParameterWithInt(fg, s.FG_CAMERA_LINK_CAMTYP,s.FG_CL_DUALTAP_8_BIT, camPort)
    err = s.Fg_setParameterWithInt(fg, s.FG_WIDTH, width, camPort)
    if (err < 0):
        print "Fg_setParameter(FG_WIDTH) failed: ", s.Fg_getLastErrorDescription(fg)
        s.Fg_FreeMemEx(fg, memHandle)
        s.Fg_FreeGrabber(fg)
        exit(err)

    err = s.Fg_setParameterWithInt(fg, s.FG_FORMAT, 3,camPort)
    err = s.Fg_setParameterWithInt(fg, s.FG_HEIGHT, height, camPort)
    if (err < 0):
        print "Fg_setParameter(FG_HEIGHT) failed: ", s.Fg_getLastErrorDescription(fg)
        s.Fg_FreeMemEx(fg, memHandle)
        s.Fg_FreeGrabber(fg)
        exit(err)

    err = s.Fg_setParameterWithInt(fg, s.FG_BITALIGNMENT, s.FG_LEFT_ALIGNED, camPort)
    if (err < 0):
        print "Fg_setParameter(FG_BITALIGNMENT) failed: ", s.Fg_getLastErrorDescription(fg)
    # s.Fg_FreeMemEx(fg, memHandle)
    # s.Fg_FreeGrabber(fg)
    # exit(err)

    if useCameraSimulator:
        # Start Generator
        s.Fg_setParameterWithInt(fg, s.FG_GEN_ENABLE, s.FG_GENERATOR, camPort)
    #	s.Fg_setParameterWithInt(fg, s.FG_GEN_ROLL, 1, camPort)
    else:
        s.Fg_setParameterWithInt(fg, s.FG_GEN_ENABLE, s.FG_CAMPORT, camPort)

    # Read back settings
    (err, oWidth) = s.Fg_getParameterWithInt(fg, s.FG_WIDTH, camPort)
    if (err == 0):
        print 'Width =', oWidth
    (err, oHeight) = s.Fg_getParameterWithInt(fg, s.FG_HEIGHT, camPort)
    if (err == 0):
        print 'Height =', oHeight
    (err, oString) = s.Fg_getParameterWithString(fg, s.FG_HAP_FILE, camPort)
    if (err == 0):
        print 'Hap File =', oString

    # create a display window
    dispId0 = s.CreateDisplay(nbBuffers * bytePerSample * samplePerPixel, width, height)
    s.SetBufferWidth(dispId0, width, height)
    # start acquisition
    err = s.Fg_AcquireEx(fg, camPort, nrOfPicturesToGrab, s.ACQ_STANDARD, memHandle)
    if (err != 0):
        print 'Fg_AcquireEx() failed:', s.Fg_getLastErrorDescription(fg)
        s.Fg_FreeMemEx(fg, memHandle)
        s.CloseDisplay(dispId0)
        s.Fg_FreeGrabber(fg)
        exit(err)

    cur_pic_nr = 0
    last_pic_nr = 0
    img = "will point to last grabbed image"
    nImg = "will point to Numpy image/matrix"

    win_name_img = "Source Image (SiSo Runtime)"
    win_name_res = "Result Image (openCV)"

    print "Acquisition started"
    image = []
    leftA = []
    rightA = []
    # RUN PROCESSING LOOP for nrOfPicturesToGrab images
    while cur_pic_nr < 300000:

        cur_pic_nr = s.Fg_getLastPicNumberBlockingEx(fg, last_pic_nr + 1, camPort, 10, memHandle)

        if (cur_pic_nr < 0):
            print "Fg_getLastPicNumberBlockingEx(", (last_pic_nr + 1), ") failed: ", (s.Fg_getLastErrorDescription(fg))
            s.Fg_stopAcquire(fg, camPort)
            s.Fg_FreeMemEx(fg, memHandle)
            s.CloseDisplay(dispId0)
            s.Fg_FreeGrabber(fg)
            exit(cur_pic_nr)

        last_pic_nr = cur_pic_nr

        # get image pointer
        img = s.Fg_getImagePtrEx(fg, last_pic_nr, camPort, memHandle)
        # handle this as Numpy array (using same memory, NO copy)\
        nImg = s.getArrayFrom(img, width, height)
        nImg = nImg[xy[0]:xy[1],xy[2]:xy[3]]
        #if cur_pic_nr == 1:

        #    ROI = cv2.selectROI(nImg)
        #    print "ROI", ROI
        nImg = cv2.medianBlur(nImg,kernel)

        #nImg = nImg[ROI[1]:ROI[3], ROI[0]:ROI[2]]
        #plt.figure(1)
        #plt.imshow(nImg)
        #plt.gray()
        #lt.show()
        a = displayThreshold(nImg, threshold, roi=None)
        b = showEyes(a,threshold,None)
        left, right = analyseFrame(nImg, threshold, None)
        plt.figure(1)
        plt.imshow(b)
        plt.gray()
        plt.pause(0.001)
        plt.clf()
        plt.figure(2)
        plt.scatter(cur_pic_nr, left, c =[1,0,0], s =1)
        plt.scatter(cur_pic_nr, right, c=[0,1,0], s =1)
        plt.figure(1)
        plt.clf()
        leftA.append(left)
        rightA.append(right)
        print left, right

        # imsave('E:/Temp Ivan/rt/' + str(last_pic_nr) + '.tif', nImg)


        # display source image
        s.DrawBuffer(dispId0, img, last_pic_nr, win_name_img)\

    s.CloseDisplay(dispId0)


    # Clean up
    #if (fg != None):
    s.Fg_stopAcquire(fg, camPort)
    print "Acquisition stopped"
    s.Fg_FreeGrabber(fg)
    s.Fg_FreeMemEx(fg, memHandle)

    print "Exited."


def start_acq(width=544, height=500):
    # Board and applet selection
    boardId = 0

    if boardId < 0:
        exit(1)

    # definition of resolution
    samplePerPixel = 1
    bytePerSample = 1
    isSlave = False
    useCameraSimulator = False
    camPort = s.PORT_A

    # number of buffers for acquisition
    nbBuffers = 8
    totalBufferSize = width * height * samplePerPixel * bytePerSample * nbBuffers

    # number of image to acquire
    nrOfPicturesToGrab = s.GRAB_INFINITE

    # Get Loaded Applet
    boardType = s.Fg_getBoardType(boardId)
    if boardType == s.PN_MICROENABLE4AS1CL:
        applet = "SingleAreaGray16"
    elif boardType == s.PN_MICROENABLE4AD1CL or boardType == s.PN_MICROENABLE4AD4CL or boardType == s.PN_MICROENABLE4VD1CL or boardType == s.PN_MICROENABLE4VD4CL:
        applet = "DualAreaGray16"
    elif boardType == s.PN_MICROENABLE4AQ4GE or boardType == s.PN_MICROENABLE4VQ4GE:
        applet = "QuadAreaGray16";
    else:
        (err, applet) = s.Fg_findApplet(boardId)
        if err != 0:
            print "No applet is found"
            exit(0)
        else:
            print 'Applet found:', applet

    # INIT FRAMEGRABBER

    print 'Initializing Board ..',

    if isSlave:
        fg = s.Fg_InitEx(applet, boardId, 1);
    else:
        fg = s.Fg_InitEx(applet, boardId, 0);

    # error handling
    err = s.Fg_getLastErrorNumber(fg)
    mes = s.Fg_getErrorDescription(err)

    if err < 0:
        print "Error", err, ":", mes
        sys.exit()
    else:
        print "ok"

    # allocating memory
    memHandle = s.Fg_AllocMemEx(fg, totalBufferSize, nbBuffers)

    # Set Applet Parameters
    err = s.Fg_setParameterWithInt(fg, s.FG_FORMAT, s.FG_GRAY, camPort)
    err = s.Fg_setParameterWithInt(fg, s.FG_CAMERA_LINK_CAMTYP, s.FG_CL_DUALTAP_8_BIT, camPort)
    err = s.Fg_setParameterWithInt(fg, s.FG_WIDTH, width, camPort)
    if (err < 0):
        print "Fg_setParameter(FG_WIDTH) failed: ", s.Fg_getLastErrorDescription(fg)
        s.Fg_FreeMemEx(fg, memHandle)
        s.Fg_FreeGrabber(fg)
        exit(err)

    err = s.Fg_setParameterWithInt(fg, s.FG_FORMAT, 3, camPort)
    err = s.Fg_setParameterWithInt(fg, s.FG_HEIGHT, height, camPort)
    if (err < 0):
        print "Fg_setParameter(FG_HEIGHT) failed: ", s.Fg_getLastErrorDescription(fg)
        s.Fg_FreeMemEx(fg, memHandle)
        s.Fg_FreeGrabber(fg)
        exit(err)

    err = s.Fg_setParameterWithInt(fg, s.FG_BITALIGNMENT, s.FG_LEFT_ALIGNED, camPort)
    if (err < 0):
        print "Fg_setParameter(FG_BITALIGNMENT) failed: ", s.Fg_getLastErrorDescription(fg)
    # s.Fg_FreeMemEx(fg, memHandle)
    # s.Fg_FreeGrabber(fg)
    # exit(err)

    if useCameraSimulator:
        # Start Generator
        s.Fg_setParameterWithInt(fg, s.FG_GEN_ENABLE, s.FG_GENERATOR, camPort)
    #	s.Fg_setParameterWithInt(fg, s.FG_GEN_ROLL, 1, camPort)
    else:
        s.Fg_setParameterWithInt(fg, s.FG_GEN_ENABLE, s.FG_CAMPORT, camPort)

    # Read back settings
    (err, oWidth) = s.Fg_getParameterWithInt(fg, s.FG_WIDTH, camPort)
    if (err == 0):
        print 'Width =', oWidth
    (err, oHeight) = s.Fg_getParameterWithInt(fg, s.FG_HEIGHT, camPort)
    if (err == 0):
        print 'Height =', oHeight
    (err, oString) = s.Fg_getParameterWithString(fg, s.FG_HAP_FILE, camPort)
    if (err == 0):
        print 'Hap File =', oString

    # create a display window
    dispId0 = s.CreateDisplay(nbBuffers * bytePerSample * samplePerPixel, width, height)
    s.SetBufferWidth(dispId0, width, height)
    # start acquisition
    err = s.Fg_AcquireEx(fg, camPort, nrOfPicturesToGrab, s.ACQ_STANDARD, memHandle)
    if (err != 0):
        print 'Fg_AcquireEx() failed:', s.Fg_getLastErrorDescription(fg)
        s.Fg_FreeMemEx(fg, memHandle)
        s.CloseDisplay(dispId0)
        s.Fg_FreeGrabber(fg)
        exit(err)

    cur_pic_nr = 0
    last_pic_nr = 0
    img = "will point to last grabbed image"
    nImg = "will point to Numpy image/matrix"

    win_name_img = "Source Image (SiSo Runtime)"
    win_name_res = "Result Image (openCV)"

    print "Acquisition started"
    image = []
    leftA = []
    rightA = []
    # RUN PROCESSING LOOP for nrOfPicturesToGrab images
    while cur_pic_nr < nrOfPicturesToGrab:

        cur_pic_nr = s.Fg_getLastPicNumberBlockingEx(fg, last_pic_nr + 1, camPort, 10, memHandle)

        if (cur_pic_nr < 0):
            print "Fg_getLastPicNumberBlockingEx(", (last_pic_nr + 1), ") failed: ", (s.Fg_getLastErrorDescription(fg))
            s.Fg_stopAcquire(fg, camPort)
            s.Fg_FreeMemEx(fg, memHandle)
            s.CloseDisplay(dispId0)
            s.Fg_FreeGrabber(fg)
            exit(cur_pic_nr)

        last_pic_nr = cur_pic_nr

        # get image pointer
        img = s.Fg_getImagePtrEx(fg, last_pic_nr, camPort, memHandle)

        # display source image
        s.DrawBuffer(dispId0, img, last_pic_nr, win_name_img)

    s.CloseDisplay(dispId0)


    print "Acquisition stopped"
    # Clean up
    # if (fg != None):
    s.Fg_stopAcquire(fg, camPort)
    s.Fg_FreeGrabber(fg)

    s.Fg_FreeMemEx(fg, memHandle)

    print "Exited."

#adjust_threshold(threshold=200, kernel=3)