#-*- coding: utf-8 -*-
import cv2
import sys
from PyQt5.QtWidgets import (QApplication, QDesktopWidget, QWidget, QGridLayout, QLabel, QComboBox, QPushButton,
                             QFileDialog, QLineEdit, QMessageBox, QProgressBar, QPlainTextEdit)


class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.video_path = ''
        self.cap=''

        #사이즈
        self.w_px = 0
        self.h_px = 0

        #시간
        self.start_time_h = 0
        self.start_time_m = 0
        self.start_time_s = 0

        self.end_time_h = 0
        self.end_time_m = 0
        self.end_time_s = 0

        #progress bar
        self.totalcount=0
        self.current_count=0

        self.img_paths={}


    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def initUI(self):
            grid = QGridLayout()
            self.setLayout(grid)
            folder_btn = QPushButton('Select Video File', self)
            folder_btn.clicked.connect(self.set_dir)

            start_btn = QPushButton('Start', self)
            start_btn.clicked.connect(self.start)


            self.line = QLineEdit()
            self.line.setReadOnly(True)

            self.w_line = QLineEdit()
            self.h_line = QLineEdit()

            self.start_time_line = QLineEdit()
            self.end_time_line = QLineEdit()

            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)

            grid.addWidget(QLabel('File Path:'), 0, 0)

            grid.addWidget(self.line, 0, 1,1,3)

            grid.addWidget(folder_btn, 1, 1,1,3)

            grid.addWidget(QLabel('가로 px:'), 2, 0)
            grid.addWidget(self.w_line, 2, 1,1,1)

            grid.addWidget(QLabel('세로 px:'), 2,2)
            grid.addWidget(self.h_line, 2,3,1,1)

            grid.addWidget(QLabel('시작 시각:'), 3, 0)
            grid.addWidget(self.start_time_line, 3, 1, 1, 1)

            grid.addWidget(QLabel('끝 시각:'), 3, 2)
            grid.addWidget(self.end_time_line, 3, 3, 1, 1)


            grid.addWidget(start_btn, 4, 1,1,3)
            grid.addWidget(self.log, 5, 1,1,3)

            self.setWindowTitle('Fan Helper')
            self.resize(500, 350)
            self.center()
            self.show()

    def trans_sec(self, hour, min, sec):
        return int(360 * hour + 60 * min + sec)

    def set_dir(self):
        self.video_path = QFileDialog.getOpenFileName(self, 'Open file', './')[0]
        self.cap = cv2.VideoCapture(self.video_path)
        self.line.setText(self.video_path)
        self.log.appendPlainText('MAX video width : ' + str(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)))
        self.log.appendPlainText('MAX video height : ' + str(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))


    def start(self):
        if self.video_path != '':
            self.log.appendPlainText('Please Wait')
            self.cap = cv2.VideoCapture(self.video_path)
            self.w_px = int(self.w_line.text())
            self.h_px = int(self.h_line.text())
            print(self.w_line.text())
            output_size=(self.w_px , self.h_px)

            fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
            out = cv2.VideoWriter('%s_output.mp4' % (self.video_path.split('.')[0]), fourcc, self.cap.get(cv2.CAP_PROP_FPS),
                                  output_size)
            if not self.cap.isOpened():
                exit()
            tracker = cv2.TrackerKCF_create()

            frame_count = 0
            self.start_time_h, self.start_time_m, self.start_time_s = map(int, self.start_time_line.text().split(':'))
            self.end_time_h, self.end_time_m, self.end_time_s = map(int, self.end_time_line.text().split(':'))
            START_SEC = self.trans_sec(self.start_time_h, self.start_time_m, self.start_time_s)
            END_SEC = self.trans_sec(self.end_time_h, self.end_time_m, self.end_time_s)
            roi_set_flag = False
            ready_flag = False
            check_mode = True


            while True:
                frame_count += 1
                ret, img = self.cap.read()

                if not ret:
                    print('cant capture')
                    exit()

                elif frame_count == START_SEC * round(self.cap.get(cv2.CAP_PROP_FPS)):  # 시작프레임
                    ret, img = self.cap.read()
                    cv2.namedWindow('Select Window')
                    cv2.imshow('Select Window', img)

                    # ROI(region of interest)설정
                    rect = cv2.selectROI('Select Window', img, fromCenter=False, showCrosshair=True)
                    cv2.destroyWindow('Select Window')
                    roi_set_flag = True
                    tracker.init(img, rect)
                    ready_flag = True
                elif frame_count == END_SEC * round(self.cap.get(cv2.CAP_PROP_FPS)):
                    break

                if roi_set_flag:
                    success, box = tracker.update(img)

                    left, top, w, h = [int(v) for v in box]
                    center_x = left + w / 2
                    center_y = top + h / 2

                    result_top = int(center_y - output_size[1] / 2)
                    result_bottom = int(center_y + output_size[1] / 2)
                    result_left = int(center_x - output_size[0] / 2)
                    result_right = int(center_x + output_size[0] / 2)

                    while result_top < 0:
                        print('top over')
                        result_top = result_top + 1
                        result_bottom = result_bottom + 1
                    while result_bottom > self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT):
                        print('bottom over')
                        result_bottom = result_bottom - 1
                        result_top = result_top - 1
                    while result_left < 0:
                        print('left over')
                        result_left = result_left + 1
                        result_right = result_right + 1
                    while result_right > self.cap.get(cv2.CAP_PROP_FRAME_WIDTH):
                        print('right over')
                        result_right = result_right - 1
                        result_left = result_left - 1

                    result_img = img[result_top:result_bottom, result_left:result_right]

                    out.write(result_img)
                    # for test
                    if check_mode:
                        cv2.rectangle(img, pt1=(left, top), pt2=(left + w, top + h), color=(255, 255, 255), thickness=3)
                        cv2.imshow('result_img', result_img)

                if ready_flag and check_mode:
                    cv2.imshow('img', img)
                    if cv2.waitKey(1) == ord('q'):
                        break
            self.log.appendPlainText('COMPLETE')
            cv2.destroyAllWindows()

def my_exception_hook(exctype, value, traceback):
    # Print the error and traceback
    print(exctype, value, traceback)
    # Call the normal Exception hook after
    sys._excepthook(exctype, value, traceback)
    # sys.exit(1)

# Back up the reference to the exceptionhook
sys._excepthook = sys.excepthook

# Set the exception hook to our wrapping function
sys.excepthook = my_exception_hook

app = QApplication(sys.argv)
ex = MyApp()
sys.exit(app.exec_())

























'''

video_path = 'test.mp4'
cap = cv2.VideoCapture(video_path)
output_size = (100, 300)

fourcc= cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
out = cv2.VideoWriter('%s_output.mp4' % (video_path.split('.')[0]), fourcc, cap.get(cv2.CAP_PROP_FPS), output_size)
if not cap.isOpened():
    exit()

tracker = cv2.TrackerKCF_create()

ret, img = cap. read()

cv2.namedWindow('Select Window')
cv2.imshow('Select Window', img)

# ROI(region of interest)설정
rect = cv2.selectROI('Select Window', img, fromCenter=False, showCrosshair=True)
cv2.destroyWindow('Select Window')

#tracker 초기화
tracker.init(img, rect)

while True:
    ret, img = cap.read()

    if not ret:
        exit()

    success, box = tracker.update(img)

    left, top, w, h = [int(v) for v in box]
    center_x = left+w/2
    center_y = top+h/2

    result_top = int(center_y - output_size[1]/2)
    result_bottom = int(center_y + output_size[1]/2)
    result_left = int(center_x - output_size[0]/2)
    result_right = int(center_x + output_size[0]/2)

    result_img = img[result_top:result_bottom, result_left:result_right]
    out.write(result_img)
    cv2.rectangle(img, pt1=(left, top), pt2=(left+w, top+h), color=(255, 255, 255), thickness=3)


    cv2.imshow('result_img', result_img)
    cv2.imshow('img', img)
    if cv2.waitKey(1) == ord('q'):
        break

'''
