import os
import sys
import numpy as np
import cv2
from ctypes import *
import matplotlib.pyplot as plt

# define parameters - 
# CHECK THAT THEY CORRESPOND ALWAYS TO THE LAST DRIVER VERSION

(CONTROL_BRIGHTNESS, # image brightness
CONTROL_CONTRAST,       # image contrast 
CONTROL_WBR,            # red of white balance 
CONTROL_WBB,            # blue of white balance
CONTROL_WBG,            # the green of white balance 
CONTROL_GAMMA,          # screen gamma 
CONTROL_GAIN,           # camera gain 
CONTROL_OFFSET,         # camera offset 
CONTROL_EXPOSURE,       # expose time (us)
CONTROL_SPEED,          # transfer speed 
CONTROL_TRANSFERBIT,    # image depth bits 
CONTROL_CHANNELS,       # image channels 
CONTROL_USBTRAFFIC,     # hblank 
CONTROL_ROWNOISERE,     # row denoise 
CONTROL_CURTEMP,        # current cmos or ccd temprature 
CONTROL_CURPWM,         # current cool pwm 
CONTROL_MANULPWM,       # set the cool pwm 
CONTROL_CFWPORT,        # control camera color filter wheel port 
CONTROL_COOLER,         # check if camera has cooler
CONTROL_ST4PORT,        # check if camera has st4port
CAM_COLOR,
CAM_BIN1X1MODE,         # check if camera has bin1x1 mode 
CAM_BIN2X2MODE,         # check if camera has bin2x2 mode 
CAM_BIN3X3MODE,         # check if camera has bin3x3 mode 
CAM_BIN4X4MODE,         # check if camera has bin4x4 mode 
CAM_MECHANICALSHUTTER,                   # mechanical shutter  
CAM_TRIGER_INTERFACE,                    # triger  
CAM_TECOVERPROTECT_INTERFACE,            # tec overprotect
CAM_SINGNALCLAMP_INTERFACE,              # singnal clamp 
CAM_FINETONE_INTERFACE,                  # fine tone 
CAM_SHUTTERMOTORHEATING_INTERFACE,       # shutter motor heating 
CAM_CALIBRATEFPN_INTERFACE,              # calibrated frame 
CAM_CHIPTEMPERATURESENSOR_INTERFACE,     # chip temperaure sensor
CAM_USBREADOUTSLOWEST_INTERFACE,         # usb readout slowest 
CAM_8BITS,                               # 8bit depth 
CAM_16BITS,                              # 16bit depth
CAM_GPS,                                 # check if camera has gps 
CAM_IGNOREOVERSCAN_INTERFACE,            # ignore overscan area 
QHYCCD_3A_AUTOBALANCE,
QHYCCD_3A_AUTOEXPOSURE,
QHYCCD_3A_AUTOFOCUS,
CONTROL_AMPV,                            # ccd or cmos ampv
CONTROL_VCAM,                            # Virtual Camera on off 
CAM_VIEW_MODE,
CONTROL_CFWSLOTSNUM,         # check CFW slots number
IS_EXPOSING_DONE,
ScreenStretchB,
ScreenStretchW,
CONTROL_DDR,
CAM_LIGHT_PERFORMANCE_MODE,
CAM_QHY5II_GUIDE_MODE,
DDR_BUFFER_CAPACITY,
DDR_BUFFER_READ_THRESHOLD
) = map(c_int, range(53))

#===============================================================================

# Load driver. Be sure that it is in the library path

qhyccd =CDLL("libqhyccd.20.4.24.dylib")

qhyccd.GetQHYCCDParam.restype=c_double
qhyccd.OpenQHYCCD.restype=POINTER(c_uint32)

# Init driver

ret=qhyccd.InitQHYCCDResource()

if ret==0:
        print("Init SDK success!\n")
else:
        print("SDK init Error")
        exit(-1)

# Look for connected camera

num=qhyccd.ScanQHYCCD()

if num>0:
     print("QHY camera found")
else:
     print("No QHY camera found")
     exit(-1)

i=c_int=0;
type_char_array_32=c_char * 32
id=type_char_array_32()

# Get camera ID and create handle for further operations

ret=qhyccd.GetQHYCCDId(i,id)
camhandle = qhyccd.OpenQHYCCD(id);

#check if camera support to get/set current temperature 
ret = qhyccd.IsQHYCCDControlAvailable(camhandle,CONTROL_CURTEMP)
if(ret==0) :
    print('Camera supports get/set temperature')
#check if camera support to get/set current PWM value
ret = qhyccd.IsQHYCCDControlAvailable(camhandle,CONTROL_CURPWM)
if(ret==0) :
    print('Camera supports get/set PWM')
#check if camera support to set the AutoMode and get the targetTemp
ret = qhyccd.IsQHYCCDControlAvailable(camhandle,CONTROL_COOLER);
if(ret==0) :
    print('Camera supports auto-thermal control and target temp')
#check if camera support to set the Manual Mode 
ret = qhyccd.IsQHYCCDControlAvailable(camhandle,CONTROL_MANULPWM)
if(ret==0) :
    print('Camera supports manual thermal control')

# Set mode and init camera

qhyccd.SetQHYCCDStreamMode(camhandle,0)
qhyccd.InitQHYCCD(camhandle)

chipw = c_double(0)
chiph = c_double(0)
w = c_uint(0)
h = c_uint(0)
pixelw = c_double(0)
pixelh = c_double(0)
bpp = c_uint(0)
channels = c_uint(0)

qhyccd.GetQHYCCDChipInfo(camhandle,byref(chipw),byref(chiph),byref(w),byref(h),byref(pixelw),
byref(pixelh),byref(bpp))

# Comment for verbose output...
qhyccd.SetQHYCCDLogLevel(0)

# Test output values. This prints meaningful numbers.

print("=================================================================")
print(w.value,h.value,pixelw.value,pixelh.value)

# Test camera features.

min_exp = c_double(0)
max_exp = c_double(0)
step_exp =c_double(0) 
ret = qhyccd.GetQHYCCDParamMinMaxStep(camhandle, CONTROL_EXPOSURE, byref(min_exp), byref(max_exp), byref(step_exp))
if(ret==0):
	print('====> Camera exposure range and step: ',min_exp,max_exp,step_exp)
else:
    qhyccd.CloseQHYCCD(camhandle)
    qhyccd.ReleaseQHYCCDResource()
    exit(1)

if (qhyccd.IsQHYCCDControlAvailable(camhandle,CONTROL_EXPOSURE)==0):
    qhyccd.SetQHYCCDParam(camhandle,CONTROL_EXPOSURE,c_double(10000.0))
else:
    print('Cannot set exposure')
    qhyccd.CloseQHYCCD(camhandle)
    qhyccd.ReleaseQHYCCDResource()
    exit(1)

if (qhyccd.SetQHYCCDBinMode(camhandle,1,1)!=0):
    print('Cannot set binning')
    qhyccd.CloseQHYCCD(camhandle)
    qhyccd.ReleaseQHYCCDResource()
    exit(1)

if(qhyccd.SetQHYCCDResolution(camhandle,0,0,w.value,h.value)!=0):
    print('Cannot set resolution')
    qhyccd.CloseQHYCCD(camhandle)
    qhyccd.ReleaseQHYCCDResource()
    exit(1)

if(qhyccd.IsQHYCCDControlAvailable(camhandle,CONTROL_TRANSFERBIT)==0):
    qhyccd.SetQHYCCDBitsMode(camhandle,16)
else:
    print('Cannot set bit depth')
    qhyccd.CloseQHYCCD(camhandle)
    qhyccd.ReleaseQHYCCDResource()
    exit(1)

min_gain = c_double(0)
max_gain = c_double(0)
step_gain =c_double(0) 

ret = qhyccd.GetQHYCCDParamMinMaxStep(camhandle, CONTROL_GAIN, byref(min_gain), byref(max_gain), byref(step_gain))
if(ret==0):
	print('====> Camera gain range and step: ',min_gain,max_gain,step_gain)
else:
    qhyccd.CloseQHYCCD(camhandle)
    qhyccd.ReleaseQHYCCDResource()
    exit(1)

ret = qhyccd.SetQHYCCDParam(camhandle,CONTROL_GAIN,4)
if(ret!=0):
    print('FAILED TO SET GAIN')
    qhyccd.CloseQHYCCD(camhandle)
    qhyccd.ReleaseQHYCCDResource()
    exit(1)
    
im_mem=qhyccd.GetQHYCCDMemLength(camhandle)
qhyccd.ExpQHYCCDSingleFrame(camhandle)

print('im_mem: ',im_mem)

#img = np.arange(0, w.value*h.value, 1, np.int16)

img = (c_uint16 * im_mem)()
width = c_uint32(w.value)
height = c_uint32(h.value)
depth = c_uint32(bpp.value)
channels = c_uint32(channels.value)

#qhyccd.GetQHYCCDSingleFrame.argtypes = [c_uint, 
#    np.ctypeslib.ndpointer(dtype=np.int32),
#    np.ctypeslib.ndpointer(dtype=np.int32),
#    np.ctypeslib.ndpointer(dtype=np.int32),
#    np.ctypeslib.ndpointer(dtype=np.int32),
#    np.ctypeslib.ndpointer(dtype=np.int16)]

#w2=h2=bpp=channels=np.array([0],dtype=np.int32)

#img = np.zeros((int(w2),int(h2)),dtype=np.int16)
print('==================================================> ',w,h,len(img))

ret = qhyccd.GetQHYCCDSingleFrame(camhandle,byref(width),byref(height),byref(depth),byref(channels),img)
if(ret!=0):
    print('FAILED TO GET SINGLE FRAME')
    qhyccd.CloseQHYCCD(camhandle)
    qhyccd.ReleaseQHYCCDResource()
    exit(1)

# print(repr(img.raw))

# print('==================================================> ',img.raw[11])

#imgbuf = np.array(img,dtype=('u8'))
realsize = height.value*width.value
print('========AFTER IMAGE ACQUISITION (H, W, bpp) ===> ',height.value,width.value,depth.value)

imgs = np.right_shift(img,4)
imgcrop = imgs[0:realsize]

imgbuf = np.array(imgcrop).reshape(height.value,width.value)

qhyccd.CloseQHYCCD(camhandle)
qhyccd.ReleaseQHYCCDResource()

print(width,height,bpp,channels)
print(im_mem, len(imgbuf))
print(imgbuf.dtype)

minim=np.min(imgbuf)
maxim=np.max(imgbuf)
rangim=maxim-minim

print("Signal range : ",minim,maxim,rangim)

#imgbuf = (imgbuf-minim)/4096*255

plt.hist(imgcrop,maxim,[minim,maxim])
plt.yscale('log')
plt.show()

#plt.hist(imgbuf,256,[0,256])
#plt.show()

dist2 = cv2.normalize(imgbuf, None, 255,0, cv2.NORM_MINMAX, cv2.CV_8UC1)
cv2.imshow('QHYCCD',dist2)

cv2.waitKey(0)
cv2.destroyAllWindows()

pixall=0
for pix in imgcrop:
	pixall = np.bitwise_or(pix,pixall)

print('Bitwise OR of all pixels: ',pixall, ' = ', np.binary_repr(pixall))



