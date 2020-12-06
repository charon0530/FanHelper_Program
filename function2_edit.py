#-*- coding: utf-8 -*-
import dlib
import cv2
import os
import pickle
import sys
import requests
import urllib.request
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PyQt5.QtWidgets import (QApplication, QDesktopWidget, QWidget, QGridLayout, QLabel, QComboBox, QPushButton,
                             QFileDialog, QLineEdit, QMessageBox, QProgressBar, QPlainTextEdit)




def hangulFilePathImageRead ( filePath ) :

    stream = open( filePath.encode("utf-8") , "rb")
    bytes = bytearray(stream.read())
    numpyArray = np.asarray(bytes, dtype=np.uint8)

    return cv2.imdecode(numpyArray , cv2.IMREAD_UNCHANGED)


class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.g_dir = ''

        #분류기
        self.file = open('model.pickle', 'rb')
        self.descs = pickle.load(self.file)
        self.file.close()

        #디렉토리
        self.file_list = ''
        self.img_list = ''

        #progress bar
        self.totalcount=0
        self.current_count=0

        self.img_paths={}



        #콤보박스


    def initUI(self):
        # 백 앤드 서버 요청
        try:
            self.response1 = requests.get(url="http://fanhelper.tk:5000/api/getGroupList")
            self.grouplist = self.response1.json()["g_list"]
            grid = QGridLayout()
            self.setLayout(grid)
            folder_btn = QPushButton('Select Folder', self)
            folder_btn.clicked.connect(self.set_dir)
            self.cb = QComboBox(self)
            self.cb.addItem('Select Group')
            for group in self.grouplist:
                self.cb.addItem(group)
            self.cb.activated[str].connect(self.onActivated)

            update_btn = QPushButton('Update', self)
            update_btn.clicked.connect(self.update)
            start_btn = QPushButton('Start', self)
            start_btn.clicked.connect(self.start)
            self.pbar = QProgressBar(self)

            self.line = QLineEdit()
            self.line.setReadOnly(True)

            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)

            grid.addWidget(QLabel('Folder Path:'), 0, 0)

            grid.addWidget(self.line, 0, 1)
            grid.addWidget(folder_btn, 1, 1)
            grid.addWidget(self.cb, 2, 1)
            grid.addWidget(update_btn, 3, 1)
            grid.addWidget(start_btn, 4, 1)
            grid.addWidget(self.pbar, 5, 1)
            grid.addWidget(self.log, 6, 1)

            self.setWindowTitle('Fan Helper')
            self.resize(500, 350)
            self.center()
            self.show()
        except:
            self.center()
            QMessageBox.question(self, 'Message', '서버연결에 실패하였습니다.', QMessageBox.Yes, QMessageBox.Yes)



    def set_dir(self):
        self.g_dir = QFileDialog.getExistingDirectory(self, 'Open Folder', './')
        self.line.setText(self.g_dir)
        self.file_list = os.listdir(self.g_dir)
        self.img_list = [file for file in self.file_list if 'jpg' in file or 'jpeg' in file or 'JPEG' in file or 'JPG' in file or
            'png' in file or 'PNG' in file]
        self.totalcount = len(self.img_list)

    def onActivated(self, text):
        self.selected_group = text
        print(text)

    def update(self):
        self.response2 = requests.post(url="http://fanhelper.tk:5000/api/memberList", data={'group': self.selected_group})
        member_list = self.response2.json()["m_list"]
        print(member_list)
        self.table = str.maketrans('\\','/')
        for memberName in member_list:
            self.changed_urls=[]
            self.res = requests.post(url="http://fanhelper.tk:5000/api/photos/getPhotoURLs", data={'group': self.selected_group, 'memberName':memberName})
            self.memberURLs = self.res.json()["m_urls"]
            for url in self.memberURLs :
                self.changed_urls.append("http://fanhelper.tk:5000/" + url.translate(self.table))

            self.img_paths[memberName] = self.changed_urls
        print(self.img_paths)
        self.create_classifier()


    def start(self):
        if self.g_dir != '' :
            self.file_list = os.listdir(self.g_dir)
            self.img_list = [file for file in self.file_list if
                             'jpg' in file or 'jpeg' in file or 'JPEG' in file or 'JPG' in file or
                             'png' in file or 'PNG' in file]

            for img_file_name in self.img_list:
                self.log.appendPlainText(img_file_name + '...')
                self.current_count = self.current_count + 1
                self.pbar.setValue(int(self.current_count/self.totalcount*100))
                print(img_file_name)
                print(self.g_dir + '/' + img_file_name)
                self.execute(self.descs, self.g_dir + '/' + img_file_name)
                self.log.appendPlainText('DONE')

            self.pbar.reset()
            self.current_count=0
            self.log.appendPlainText('COMPLETE')

        QMessageBox.question(self, 'Message', 'Complete', QMessageBox.Yes, QMessageBox.Yes)


    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def find_faces(self,img):
        detector = dlib.get_frontal_face_detector()
        sp = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
        dets = detector(img, 1)

        if len(dets) == 0:
            return np.empty(0), np.empty(0), np.empty(0), len(dets)

        rects, shapes = [], []  # shapes = landmarks of faces
        shapes_np = np.zeros((len(dets), 68, 2), dtype=np.int)
        for k, d in enumerate(dets):
            rect = ((d.left(), d.top()), (d.right(), d.bottom()))
            rects.append(rect)

            shape = sp(img, d)  # return full object dectection(landmarks)

            for i in range(0, 68):
                shapes_np[k][i] = (shape.part(i).x, shape.part(i).y)

            shapes.append(shape)
        return rects, shapes, shapes_np, len(dets)

    def encode_face(self,img, shapes):
        facerec = dlib.face_recognition_model_v1('dlib_face_recognition_resnet_model_v1.dat')
        face_descriptors = []
        for shape in shapes:
            face_descriptor = facerec.compute_face_descriptor(img, shape)
            face_descriptors.append(np.array(face_descriptor))
        return np.array(face_descriptors)

    def url_to_image(self,url):
        # download the image, convert it to a NumPy array, and then read
        # it into OpenCV format
        resp = urllib.request.urlopen(url)
        image = np.asarray(bytearray(resp.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        # return the image
        return image

    def create_classifier(self):  # 분류기 생성을 위한 코드
        descs = {}
        p_bar_count=0
        for name, img_path_list in self.img_paths.items():
            count = 0
            descs[name] = []
            for img_path in img_path_list:
                img_bgr = self.url_to_image(img_path)
                img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                _, img_shapes, _, face_num = self.find_faces(img_rgb)
                p_bar_count = p_bar_count+1
                self.pbar.setValue(int(p_bar_count / (len(self.img_paths)*len(img_path_list)) * 100))
                # 얼굴을 못찾았을 때
                if face_num == 0:
                    count += 1
                    print(name, count, 'Face Detect Fail')
                    continue
                elif face_num != 1:
                    count += 1
                    print(name, count, 'Too Many Faces')
                    continue
                descs[name].append(self.encode_face(img_rgb, img_shapes)[0])
                count += 1
                print(name, count, 'finish')

        self.pbar.reset()
        pickle_file = open('model.pickle', 'wb')
        pickle.dump(descs, pickle_file)
        pickle_file.close()
        self.file = open('model.pickle', 'rb')
        self.descs = pickle.load(self.file)
        self.file.close()
        QMessageBox.question(self, 'Message', 'Complete', QMessageBox.Yes, QMessageBox.Yes)


    def execute(self, classfier_desc, img_path):
        # 테스트할 사진 인코딩
        img_bgr = hangul_imread(img_path)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

        rects, shapes, _, face_num = self.find_faces(img_rgb)

        if face_num == 0:
            print("Face Detect Fail")
            return

        descriptors = self.encode_face(img_rgb, shapes)

        fig, ax = plt.subplots(1, figsize=(20, 20))
        ax.imshow(img_rgb)

        tag = ''
        for i, desc in enumerate(descriptors):
            out_name = ''
            pre_dist = float(9999999999)
            found = False
            for name, saved_descs in classfier_desc.items():
                # print(name)
                # print()
                for saved_desc in saved_descs:
                    dist = np.linalg.norm([desc] - saved_desc, axis=1)
                    # 하한 값 설정
                    if dist < 0.5:  # 0.6:
                        found = True
                        if out_name == '':  # 처음발견
                            # print(out_name, name, dist, pre_dist)
                            out_name = name
                            pre_dist = dist

                        elif pre_dist > dist:
                            # print(name, out_name, pre_dist, dist)
                            pre_dist = dist
                            if out_name != name:
                                # print(name, out_name)
                                out_name = name

            if found:
                # 동작을 확인하기 위한 코드

                text = ax.text(rects[i][0][0], rects[i][0][1], out_name, color='b', fontsize=30)
                rect = patches.Rectangle(rects[i][0],
                                         rects[i][1][1] - rects[i][0][1],
                                         rects[i][1][0] - rects[i][0][0],
                                         linewidth=2, edgecolor='w', facecolor='none')
                ax.add_patch(rect)

                if tag == '':
                    tag = out_name
                else:
                    tag = tag + ',' + out_name
            # break

            if not found:
                text = ax.text(rects[i][0][0], rects[i][0][1], "unknown", color='b', fontsize=30)
                rect = patches.Rectangle(rects[i][0],
                                         rects[i][1][1] - rects[i][0][1],
                                         rects[i][1][0] - rects[i][0][0],
                                         linewidth=2, edgecolor='r', facecolor='none')
                ax.add_patch(rect)

        if tag != '':
            folder = img_path.split('/')[:-1]
            file_name = img_path.split('/')[-1]
            folder = '/'.join(folder)
            print(folder)
            print(file_name)
            print(tag)
            os.rename(img_path, folder + '/' + 'TAG_' + tag + '_' + file_name)
        elif tag == '':
            print('Unknown')

def hangul_imread(filename, flags=cv2.IMREAD_COLOR, dtype=np.uint8):
    try:
        n = np.fromfile(filename, dtype)
        img = cv2.imdecode(n, flags)
        return img
    except Exception as e:
        print(e)
        return None

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