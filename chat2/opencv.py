import cv2 as cv
import numpy as np


if __name__ == "__main__":
    img = cv.imread('img/bg/八重神子背景.png')
    kernel = np.ones((5, 5), np.float32)/25
    # 注意哦，内核应该保证内核每一个值之和为1
    #print("原图形:\n", img[:, :, 2], end='\n'*4)   # 输出比较处理前后的像素信息发生的变化
    dst = cv.filter2D(img, -1, kernel)
    #print("处理后的图形:\n", dst[:, :, 2])

    cv.imshow('imag1', img)
    cv.imshow('imag2', dst)
    cv.waitKey(0)
    cv.destroyAllWindows()
