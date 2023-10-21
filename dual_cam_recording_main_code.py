from flir_sidecamera_Acquire_tools import *
from backcamera_Acquire_tools import *
import u3
from datetime import datetime
import time
import threading
import os

Fish_Index = 'F4_1_3_UVRed'

Date = datetime.today().strftime('%Y-%m-%d')
Saving_Directory = 'E:\\Temp_Can\\' + Date + '\\HSA\\BEHAVIOR\\'+ 'SIDECAMERA\\' + Fish_Index + '\\'
Saving_Directory1 = 'E:\\Temp_Can\\' + Date + '\\HSA\\BEHAVIOR\\'+ 'TOPCAMERA\\' + Fish_Index + '\\'

if not os.path.exists(Saving_Directory1):
    os.makedirs(Saving_Directory1)

# parameters of top camera
width = 544
height = 550


trial_num = 30
trial_duration = 2000
IBI = 40 # rest 60s after each trial
create_directory(Saving_Directory)

# -------------------------------------------------------------------------------------------
# INITIALIZE LABJACK
dev = u3.U3()
dev.getCalibrationData()
dt = 10
#dev.configIO(EnableCounter1=True, TimerCounterPinOffset=7)


# Main loop for trials-----------------------------------------------------------------------
trial_index = 0

# trials start here

# -------------------------------------------------------------------------------------------
# DEFINE DUAL CAMs FUNCTION

def multi_cam(cam_i):
    if cam_i == 0:

        for i, cam in enumerate(cam_list):
            print('Running example for camera %d...' % i)
            t0_d = run_single_camera(cam, nodemap, nImages=trial_duration, filename=Saving_Directory + "FLIR_"+Date+"_"+Fish_Index+"-T" + str(trial_index + 1))
            print('Camera %d example complete... \n' % i)
        # main_acquisition(fps=100, gain=0., exposure=150, nImages=trial_duration,filename=Saving_Directory + "FLIR_"+Date+"_"+Fish_Index+"-T" + str(trial_index + 1))

        print('FLIR cam total time is ' + str(t0_d) + 's')
    if cam_i == 1:
        t1 = time.time()
        Start_Trial(trial_index + 1, Fish_Index, Date, trial_duration, Saving_Directory1, width, height)
        t1_d = time.time() - t1
        print('top cam total time is ' + str(t1_d) + 's')


# initiate a new trial
while trial_index < trial_num:
    # record the time of initiation
    now = datetime.now()
    print(now.strftime('%H:%M:%S'))
    print('now running trial ' + str(trial_index+1))
    with open(Saving_Directory + 'Recording_log' + Date + '_' + Fish_Index + '.txt', 'a') as f:
        f.writelines('Trial ' + str(trial_index) + ', Triggered when ' + now.strftime('%H:%M:%S') + '\n')

    # setup FLIR camera
    cam, cam_list, nodemap, system = FLIR_INIT(fps=200, gain=9.3, exposure=2000)
    #print("here")
    #print(cam.AcquisitionResultingFrameRate())
    # print('FLIR FRAME RATE IS '+str(cam.AcquisitionFrameRate))
    # setup top camera
    Setup_camera(width, height)

    # send TTL to projector
    dev.setDOState(ioNum=7, state=0)
    dev.getFeedback(u3.WaitShort(dt))
    dev.setDOState(ioNum=7, state=1)
    dev.getFeedback(u3.WaitShort(dt))
    dev.setDOState(ioNum=7, state=0)

    # start the recording of exp
    hThreadHandle_0 = threading.Thread(target=multi_cam, args=(0,))
    hThreadHandle_1 = threading.Thread(target=multi_cam, args=(1,))
    hThreadHandle_1.start()
    hThreadHandle_0.start()
    hThreadHandle_1.join()
    hThreadHandle_0.join()
    trial_index += 1
    # deInit both camera
    Turn_off_camera()
    del cam
    FLIR_DEINIT(cam_list, system)



    time.sleep(IBI)
print('Experiment is complete!')


























































































































































































############## begin here ############










































































































































































































