import cv2 as cv
import numpy as np

cap = cv.VideoCapture(0, cv.CAP_V4L2)

cap.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc('B', 'G', 'R', '3'))
cap.set(cv.CAP_PROP_FRAME_WIDTH, 160)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 120)
cap.set(cv.CAP_PROP_CONVERT_RGB, 0) 

while True:
    ret, frame = cap.read()
    frame = cv.resize(frame, (640, 480), interpolation=cv.INTER_CUBIC)

    cv.imshow('frame', frame)

    if cv.waitKey(1) & 0xFF == ord('q'):
        break


cap.release()
cv.destroyAllWindows()