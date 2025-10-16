import cv2 as cv
import numpy as np

# Camera parameters
camera_matrix = np.array([[104.65403680863373, 0.0, 79.21313258957062],
                         [0.0, 104.48251047202757, 55.689070170705634],
                         [0.0, 0.0, 1.0]])

distortion_coeff = np.array([[-0.39758308581607127,
                             0.18068641745671193,
                             0.004626461618389028,
                             0.004197358204037882,
                             -0.03381399499591463]])

new_camera_matrix = np.array([[66.54581451416016, 0.0, 81.92717558174809],
                             [0.0, 64.58526611328125, 56.23740168870427],
                             [0.0, 0.0, 1.0]])

cap = cv.VideoCapture(0)

while True:
    ret, img = cap.read()
    
    # Undistort image
    undistorted_img = cv.undistort(img, camera_matrix, distortion_coeff, None, new_camera_matrix)
    img = cv.resize(img, (720, 640), interpolation=cv.INTER_CUBIC)
    undistorted_img = cv.resize(undistorted_img, (720, 640), interpolation=cv.INTER_CUBIC)
    # Show both images
    cv.imshow('Original', img)
    cv.imshow('Undistorted', undistorted_img)
    
    # Press 'q' to quit, 's' to save
    key = cv.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        cv.imwrite('original.jpg', img)
        cv.imwrite('undistorted.jpg', undistorted_img)
        print("Images saved!")

cap.release()
cv.destroyAllWindows()