import cv2
import numpy as np
from matplotlib import pyplot as plt
from skimage import measure
import imutils
from imutils import contours
import math
import tifffile

def findMidpoint(*points):
    n = len(points)
    xs, ys = zip(*points)
    x = sum(xs) * (1.0/n)
    y = sum(ys) * (1.0/n)
    return (x, y)

def vector(a, b):
    dx = float(b[0]) - float(a[0])
    dy = float(b[1]) - float(a[1])
    return (dx, dy)


def angleAB(a, b):
    dx, dy = vector(a, b)
    angle = math.atan2(dy, dx)
    if angle < 0:
        angle += (2 * math.pi)
    return angle

def distance(a, b):
    '''Pythagoras: finds the distance between two points (a1, a2), (b1, b2)'''
    deltax2 = (b[0]-a[0])**2
    deltay2 = (b[1]-a[1])**2
    ab = math.sqrt(deltax2 + deltay2)
    return ab

def cropImage(image, ROI):
    x1, y1 = ROI[0]
    x2, y2 = ROI[1]
    cropped = image[y1:y2+1, x1:x2+1]
    return cropped

def applyThreshold(image, value, threshold='to_zero'):
    if threshold == 'to_zero':
        ret, new = cv2.threshold(image, value, 255, cv2.THRESH_TOZERO)
    elif threshold == 'otsu':
        ret, new = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif threshold == 'binary':
        ret, new = cv2.threshold(image, value, 255, cv2.THRESH_BINARY)
    else:
        new = image
    #print('new shape is '+str(new.shape))
    new = new.astype('uint8')
    return new

def contourCentre(contour):
    moments = cv2.moments(contour)
    if moments["m00"] != 0:
        c = moments["m10"] / moments["m00"], moments["m01"] / moments["m00"]
    else:
        if len(contour) == 1:
            c = tuple(contour.squeeze().tolist())
        else:
            points = contour.squeeze().tolist()
            c = findMidpoint(*points)
    return c

def findSwimBladder(contours):
    cs = [contourCentre(cnt) for cnt in contours]
#     print(len(cs))
    ds = [distance(p1, p2) for p1, p2 in zip([cs[0], cs[0], cs[1]], [cs[1], cs[2], cs[2]])]
    shortest_i = ds.index(min(ds))
    sb_i = 2-shortest_i
    return sb_i

def findContours(image, image1):
    # new = np.copy(image)
    thresh = cv2.erode(image, None, iterations=2)
    thresh = cv2.dilate(thresh, None, iterations=5)

    # perform a connected component analysis on the thresholded
    # image, then initialize a mask to store only the "large"
    # components
    labels = measure.label(thresh, background=0)

    mask = np.zeros(thresh.shape, dtype="uint8")


    # loop over the unique components
    for label in np.unique(labels):
        # if this is the background label, ignore it
        if label == 0:
            continue

        # otherwise, construct the label mask and count the
        # number of pixels
        labelMask = np.zeros(thresh.shape, dtype="uint8")
        labelMask[labels == label] = 255
        numPixels = cv2.countNonZero(labelMask)

        # if the number of pixels in the component is sufficiently
        # large, then add it to our mask of "large blobs"
        if numPixels > 70:
            mask = cv2.add(mask, labelMask)
    # plt.imshow(mask,'gray')
    # plt.show()
    # find the contours in the mask, then sort them from left to
    # right
    mask2 = mask.copy()
    # cnts, hierarchy = cv2.findContours(mask2, cv2.RETR_EXTERNAL,
    #                         cv2.CHAIN_APPROX_SIMPLE)
    cnts = cv2.findContours(mask2, cv2.RETR_TREE,
                            cv2.CHAIN_APPROX_SIMPLE)
    # print(cnts)
    cnts = cnts[1]
    # cv2.drawContours(mask2,cnts,-1,(100,100,100),5)
    # plt.imshow(mask2)
    # plt.show()
    # plt.imshow(mask)
    # plt.show()
#     cnts = cnts[0] if imutils.is_cv2() else cnts[1]
#     print(cnts)
    cnts = contours.sort_contours(cnts)[0]


    # loop over the contours
    # for (i, c) in enumerate(cnts):
    #     # draw the bright spot on the image
    #     (x, y, w, h) = cv2.boundingRect(c)
    #     ((cX, cY), radius) = cv2.minEnclosingCircle(c)
    #
    #     cv2.circle(image, (int(cX), int(cY)), int(radius),
    #                (0, 0, 255), 3)
    #     cv2.putText(image, "#{}".format(i + 1), (x, y - 15),
    #                 cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)

    # show the output image
    #cv2.imshow("Image", image)

    #np.set_printoptions(threshold=np.nan)
    #print new
    #contours, hierarchy = cv2.findContours(new, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    # use this code to show binary result
    cnt= sorted(cnts, key=lambda contour: cv2.contourArea(contour))
    # Ishraq start
    # mask3 = mask.copy()
    # cv2.drawContours(mask3,cnt[:3],-1,(100,100,100),5)
    # plt.imshow(mask3)
    # plt.show()
    #end
    return cnt

def findAllContours(image, thresh):
    threshed = applyThreshold(image, thresh, 'binary')
    contours = findContours(threshed,image)
    internals = contours[:3]
    
    return internals

def analyseFrame(frame, thresh, roi):
    """
    Main analysis function
    :param video: Video class object (video_handling)
    :param thresh: threshold used to find eyes and swimbladder
    :param roi: crop each frame to ROI (if None then video is not cropped)
    :return: pandas DataFrame (frame number and vergence angles)y

    """
    image = frame  # video.grabFrameN(frame)
    if roi is not None:
        image = cropImage(image, roi)
#     print(image.shape)
    contours = findAllContours(image, thresh=thresh)
    sb_i = findSwimBladder(contours)
    sb = contours[sb_i]
    c = contourCentre(sb)

    eye_cs = [contourCentre(eye) for eye in contours]
    eye_c_xs, eye_c_ys = zip(*eye_cs)
    mp = findMidpoint(*eye_cs)
#     print('swimming bladder center is ')
#     print(c)
#     print('eye mid point is')
#     print(mp)
    orientation = np.rad2deg(angleAB(mp, c))-90
    
    return orientation,c,contours

def compute_orientation(img,roi,threshold):
    img_blurred = cv2.medianBlur(img,5)
    try:
        orientation,c,contours = analyseFrame(img_blurred, threshold, roi)
        if len(contours) == 3:
            for i in range(0,len(contours)):
                if cv2.contourArea(contours[i])<150 or cv2.contourArea(contours[i])>2000:
                    print('contour area is ' + str(cv2.contourArea(contours[i])))
                    print('bad orientation is '+str(orientation))
                    return False
                if np.all(contours[i][0] == [0,0]):
                    print('the contour is not enough, bad orientation is ' + str(orientation))
                    return False
            return orientation,c
        else:
            print('contour number is less than 3')
            return False
    except:
        print('cant compute contours and orientation')
        return False

