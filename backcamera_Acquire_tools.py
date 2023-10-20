# Import---------------------------------------------------------------------------------
from realtime_adjust_parameters import *
import h5py
import os
import SiSoPyInterface as s
from tracker_helpers import *
from psychopy import visual, core, event, monitors, sound, constants
from win32api import GetSystemMetrics


#Functions:

def Analyze_Frame_Orientation(width, height, searching_duration, orientation_thresh, position_thresh, binary_thresh,
                              consecutive, saving_dir, baseline_duration):
    """
    Draw a frame using Draw_Frame(), convert into ndarray, crop the position_thresh, binarize the frame, find the object using fish size, calculate orientation and centroid
    save frames to saving dir
    :param trial_index: the index of the current trial
    :param Fish_Index: the index of the fish
    :param saving_dir: the saving directory for frames and the analyzed data
    :param searching_duration: the longest in terms of second to search for a good position, otherwise abolish the experiment
    :param orientation: the leftward most and rightward most orientation of fish to trigger the trial
    :param position_thresh: the left most, right most, up most, down most in mm for head position to trigger the trial
    :return: whether fish in good position and orientation to start trial, and save the frames as the baseline video to saving dir
    """
    # initialization
    global buffer_frame_index
    global buffer_size
    global buffer_dir

    last_pic_nr = 0
    last_buffer_frame_index = 0
    Setup_camera(width, height)
    consec = 0
    buffer_dir = saving_dir + 'buffer' + '.h5'
    # create empty h5 buffer
    buffer_size = [baseline_duration, width, height]
    empty_frame = Draw_Frame(width, height,last_pic_nr)[0]

    hdf = h5py.File(buffer_dir, 'w')
    for i in range(0,buffer_size[0]):
        hdf.create_dataset(str(i), data = empty_frame)
    hdf.close()

    while last_pic_nr <= searching_duration:
        #first draw one frame from the camera

        frame = Draw_Frame(width, height,last_pic_nr)
        last_pic_nr = frame[1]
        buffer_frame_index = last_pic_nr % buffer_size[0]

        with h5py.File(buffer_dir, 'r+') as hdf:
            for f in range(last_buffer_frame_index + 1, buffer_frame_index + 1):
                data = hdf[str(f)]  # load the data
                data[...] = frame[0]
        hdf.close()

        # print('last bfi is ' + str(last_buffer_frame_index))
        # print('last pic number is ' + str(last_pic_nr))
        # print('bfi is ' + str(buffer_frame_index))

        last_buffer_frame_index = buffer_frame_index

        #then calculate the orientation of the fish, if fish not in range then return False
        analyze_frame = compute_orientation(frame[0], position_thresh, binary_thresh)
        print(analyze_frame)


        if analyze_frame:
            # break the loop if found good position
            if analyze_frame[0] > orientation_thresh[0] and analyze_frame[0] < orientation_thresh[1]:
                consec += 1
                if consec >= consecutive:
                    return True
            else:
                consec = 0
    print('no good position found')
    return False


def create_directory(path):
    """
    Create directory if it does not exists.
    :param path: path of the directory
    :return: False if directory already exists, True otherwise
    """
    if os.path.exists(path):
        return False
    os.makedirs(path)
    return True


def Draw_Frame(width = 600, height = 800, last_pic_nr = 0):
    '''
    draw a single frame from camera
    :param nframe:
    :param width:
    :param height:
    :return:
    '''

    global fg
    global camPort
    global memHandle
    global dispId0

    cur_pic_nr = s.Fg_getLastPicNumberBlockingEx(fg, last_pic_nr + 1, camPort, 10, memHandle)
    img = s.Fg_getImagePtrEx(fg, cur_pic_nr, camPort, memHandle)
    nImg = s.getArrayFrom(img, width, height)

    # display source image
    s.DrawBuffer(dispId0, img, cur_pic_nr,'')
    return [nImg, cur_pic_nr]

def save_baseline(Saving_Directory,Date,Fish_Index, trial_index):
    global buffer_frame_index
    global buffer_size
    global buffer_dir

    file_name_bl = Date + '_' + Fish_Index + '_Trial' + str(trial_index+1) + '_Baseline'
    #sort index
    hdf = h5py.File(Saving_Directory + file_name_bl + '.h5', 'w')
    hdf.close
    index = 0
    for i in range(buffer_frame_index ,buffer_size[0]):
        print(i)
        print(index)
        with h5py.File(buffer_dir, 'r') as hdf:
            datahdf = hdf[str(i)]
            frame = datahdf[:]
        hdf.close

        with h5py.File(Saving_Directory + file_name_bl + '.h5', 'r+') as hdf:
            hdf.create_dataset(str(index), data = frame)
        hdf.close()
        index += 1

    for i in range(0, buffer_frame_index):
        print(i)
        print(index)
        with h5py.File(buffer_dir, 'r') as hdf:
            datahdf = hdf[str(i)]
            frame = datahdf[:]
            frame.shape
        hdf.close

        with h5py.File(Saving_Directory + file_name_bl + '.h5', 'r+') as hdf:
            hdf.create_dataset(str(index), data = frame)
        hdf.close()
        index += 1

def Setup_camera(width, height):

    """
    setup the camera
    :return: None
    """

    global fg
    global camPort
    global memHandle
    global dispId0

    # Board and applet selection
    boardId = 0

    # definition of resolution
    samplePerPixel = 1
    bytePerSample = 1
    isSlave = False
    useCameraSimulator = False
    camPort = s.PORT_A

    # number of buffers for acquisition
    nbBuffers = 8
    totalBufferSize = width * height * samplePerPixel * bytePerSample * nbBuffers

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
    err = s.Fg_AcquireEx(fg, camPort, s.GRAB_INFINITE, s.ACQ_STANDARD, memHandle)
    if (err != 0):
        print 'Fg_AcquireEx() failed:', s.Fg_getLastErrorDescription(fg)
        s.Fg_FreeMemEx(fg, memHandle)
        s.CloseDisplay(dispId0)
        s.Fg_FreeGrabber(fg)
        exit(err)

    return


def Start_Trial_h5(trial_index, Fish_Index, Date, trial_duration, Saving_Directory, width, height):
    """
    :param trial_index:
    :param Fish_Index:
    :param Date:
    :param trial_duration:
    :param saving_dir:
    :return:
    """
    global fg
    global camPort
    global memHandle
    global dispId0

    cur_pic_nr = 0
    last_pic_nr = 0
    pic_diff = s.Fg_getLastPicNumberBlockingEx(fg, 0, camPort, 10, memHandle)

    file_name = Date +'_' + Fish_Index + '_Trial' + str(trial_index)
    with h5py.File(Saving_Directory + file_name + '.h5', 'w') as hdf:
        while cur_pic_nr < trial_duration + pic_diff:

            cur_pic_nr = s.Fg_getLastPicNumberBlockingEx(fg, last_pic_nr + 1, camPort, 10, memHandle)
            last_pic_nr = cur_pic_nr

            # get image pointer
            img = s.Fg_getImagePtrEx(fg, last_pic_nr, camPort, memHandle)
            nImg = s.getArrayFrom(img, width, height)
            print('it is trial '+ str(trial_index) + ', and the frame num is ' + str(cur_pic_nr))

            #print 'start'
            hdf.create_dataset(str(last_pic_nr - pic_diff), data= nImg )

            # display source image
            s.DrawBuffer(dispId0, img, last_pic_nr, file_name)
    hdf.close()
    return

def Start_Trial(trial_index, Fish_Index, Date, trial_duration, Saving_Directory, width, height):
    """
    :param trial_index:
    :param Fish_Index:
    :param Date:
    :param trial_duration:
    :param saving_dir:
    :return:
    """
    global fg
    global camPort
    global memHandle
    global dispId0

    cur_pic_nr = 0
    last_pic_nr = 0
    frame = 0
    file_name = Date + '_' + Fish_Index + '_Trial' + str(trial_index)
    print(Saving_Directory + file_name + '.mp4')
    output = cv2.VideoWriter(Saving_Directory + file_name + '.mp4', cv2.VideoWriter_fourcc(*'mp4v'),200,(width,height),False)
    while frame <= trial_duration:
        cur_pic_nr = s.Fg_getLastPicNumberBlockingEx(fg, last_pic_nr + 1, camPort, 10, memHandle)
        last_pic_nr = cur_pic_nr

        # get image pointer
        img = s.Fg_getImagePtrEx(fg, last_pic_nr, camPort, memHandle)
        nImg = s.getArrayFrom(img, width, height)
        print('it is trial '+ str(trial_index) + ', and the frame num is ' + str(frame))

        #print 'start'
        output.write(nImg)

        # display source image
        s.DrawBuffer(dispId0, img, last_pic_nr, file_name)
        frame += 1
    output.release()
    return

def Start_Trial_OMR(trial_index, Fish_Index, Date, trial_duration, Saving_Directory, width, height,win_OMR, Video_Directory):
    """
    :param trial_index:
    :param Fish_Index:
    :param Date:
    :param trial_duration:
    :param saving_dir:
    :return:
    """
    global fg
    global camPort
    global memHandle
    global dispId0

    cur_pic_nr = 0
    last_pic_nr = 0
    pic_diff = s.Fg_getLastPicNumberBlockingEx(fg, 0, camPort, 10, memHandle)
    # if trial_index%2 == 1:
    mov_OMR = visual.MovieStim3(win_OMR, Video_Directory + 'Grating_Sin_30DPS.mp4')
    # mov_OMR = visual.Circle(win=win_OMR, lineWidth=0, radius=150,
    #                          units='degFlat', fillColor=[1, 0, 1], pos=[0, 0])
    # else:
    #     mov_OMR = visual.MovieStim3(win_OMR, Video_Directory + 'No_Stimulus.mp4')
    print('check')
    t0 = time.time()
    i=0
    file_name = Date +'_' + Fish_Index + '_Trial' + str(trial_index)
    with h5py.File(Saving_Directory + file_name + '.h5', 'w') as hdf:
        while cur_pic_nr < trial_duration + pic_diff:
            t = time.time() - t0
            print(t)
            mov_OMR.draw()
            win_OMR.flip()
            cur_pic_nr = s.Fg_getLastPicNumberBlockingEx(fg, last_pic_nr + 1, camPort, 10, memHandle)
            last_pic_nr = cur_pic_nr
            # get image pointer
            img = s.Fg_getImagePtrEx(fg, last_pic_nr, camPort, memHandle)
            nImg = s.getArrayFrom(img, width, height)
            print(cur_pic_nr)
            #print 'start'
            hdf.create_dataset(str(last_pic_nr - pic_diff), data= nImg )
            print(i)
            i+=1
            # display source image
            s.DrawBuffer(dispId0, img, last_pic_nr, file_name)
    hdf.close()
    return


def Turn_off_camera():
    '''
    turn off the camera
    :return:
    '''
    global fg
    global camPort
    global memHandle
    global dispId0

    # Clean up
    # if (fg != None):
    s.CloseDisplay(dispId0)
    s.Fg_stopAcquire(fg, camPort)
    print "Acquisition stopped"
    s.Fg_FreeGrabber(fg)
    s.Fg_FreeMemEx(fg, memHandle)
    return
