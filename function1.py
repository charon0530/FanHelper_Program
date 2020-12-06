import os
import PIL.Image as image
import PIL.ExifTags
import sys
from PyQt5.QtWidgets import (QApplication, QDesktopWidget, QWidget, QGridLayout, QLabel, QComboBox, QPushButton,
                             QFileDialog, QLineEdit, QMessageBox)

g_dir = ''
g_mode_num = 999

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.grid = QGridLayout()
        self.setLayout(self.grid)

        self.folder_btn = QPushButton('Select Folder', self)
        self.folder_btn.clicked.connect(self.set_dir)
        self.start_btn = QPushButton('Start', self)
        self.start_btn.clicked.connect(self.start)

        self.line = QLineEdit()
        self.line.setReadOnly(True)
        self.cb = QComboBox(self)
        self.cb.addItem('select')
        self.cb.addItem('year')
        self.cb.addItem('month')
        self.cb.addItem('day')
        self.cb.activated[str].connect(self.onActivated)


        self.grid.addWidget(QLabel('Folder Path:'), 0, 0)
        self.grid.addWidget(QLabel('Mode:'), 2, 0)

        self.grid.addWidget(self.line, 0, 1)
        self.grid.addWidget(self.folder_btn, 1, 1)
        self.grid.addWidget(self.cb, 2, 1)
        self.grid.addWidget(self.start_btn, 3, 1)

        self.setWindowTitle('Fan Helper')
        self.resize(500, 350)
        self.center()
        self.show()

    def set_dir(self):
        global g_dir
        g_dir = QFileDialog.getExistingDirectory(self, 'Open Folder', 'c:/')
        self.line.setText(g_dir)


    def start(self):
        global g_dir, g_mode_num
        if g_dir != '' and g_mode_num in [1, 2, 3]:
            main()
        reply = QMessageBox.question(self, 'Message', 'Complete',
                                     QMessageBox.Yes, QMessageBox.Yes)

    def onActivated(self, text):
        global g_mode_num
        if text == 'year':
            g_mode_num = 1
        elif text == 'month':
            g_mode_num = 2
        elif text == 'day':
            g_mode_num = 3
        else:
            g_mode_num = 998

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

def main():
    # path_dir = input('input folder path')
    # file list = 사진이 모여있는 디렉토리의 파일명들
    # file = file_list의 각각의 파일
    # 파일 확장자가 jpg 또는 png 파일 리스트
    #path_dir = './test/img'
    global g_dir
    global g_mode_num
    path_dir = g_dir
    print(path_dir)
    mode_num = g_mode_num
    file_list = os.listdir(path_dir)
    print(file_list)
    img_list = [file for file in file_list if 'jpg' in file or 'jpeg' in file or 'JPEG' in file or 'JPG' in file or
                'png' in file or 'PNG' in file]

    # print(img_list)

    if not img_list:
        print('No Image')
        return -9

    print('Images counts = ', len(img_list))

    #mode_num = int(input('1. year // 2. month // 3. day  '))

    # 각각의 사진에 exif 정보 접근
    for img_file_name in img_list:
        opened_img = image.open(path_dir + '/' + img_file_name)
        info = opened_img._getexif()

        exif = {
            PIL.ExifTags.TAGS[k]: v for k, v in info.items() if k in PIL.ExifTags.TAGS
        }

        if 'DateTimeOriginal' in exif:
            # 사진 생성 날짜 추출
            date_tmp = exif['DateTimeOriginal'].split()[0]
            date = date_tmp.replace(':', '_')
            # print(date)
            date_year, date_month, date_day = date.split('_')
            # print(date_year, date_month, date_day)

            if mode_num == 1:
                mode = date_year
            elif mode_num == 2:
                mode = date_year+'_'+date_month
            elif mode_num == 3:
                mode = date_year+'_'+date_month+'_'+date_day
            else:
                print('mode_num Error // mode_num =', mode_num)
                return -8

            if mode not in file_list:
                os.mkdir(path_dir + '/' + mode)
                file_list = os.listdir(path_dir)
                print('create folder')
                opened_img.close()
                os.rename(path_dir + '/' + img_file_name, path_dir + '/' + mode + '/' + img_file_name)
            # 해당 날짜 폴더가 있을 경우
            else:
                opened_img.close()
                os.rename(path_dir + '/' + img_file_name, path_dir + '/' + mode + '/' + img_file_name)


app = QApplication(sys.argv)
ex = MyApp()
sys.exit(app.exec_())



