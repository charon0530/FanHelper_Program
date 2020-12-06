import dlib
import cv2
import os
import pickle
import statistics
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

#전역변수(classfier생성에 사용)


def getdirpath(path):
    dir_path = [path + '/' + file_name for file_name in os.listdir(path) if 'jpg' in file_name or 'jpeg' in file_name
                or 'JPEG' in file_name or 'JPG' in file_name or 'PNG' in file_name or 'png' in file_name]
    return dir_path


img_paths = {
    'DS': getdirpath('./BIGBANG/DS'),
    'GD': getdirpath('./BIGBANG/GD'),
    'SL': getdirpath('./BIGBANG/SL'),
    'TY': getdirpath('./BIGBANG/TY'),
    'TOP': getdirpath('./BIGBANG/top')
}

def find_faces(img):
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

def encode_face(img, shapes):
    facerec = dlib.face_recognition_model_v1('dlib_face_recognition_resnet_model_v1.dat')
    face_descriptors = []
    for shape in shapes:
        face_descriptor = facerec.compute_face_descriptor(img, shape)
        face_descriptors.append(np.array(face_descriptor))
    return np.array(face_descriptors)


def distance_from_zero(vector):
    '''
    :param vector: 원점으로부터 거리 구하는 함수 , sort key값으로 이용하기
    :return:
    '''

def create_classifier():                            #분류기 생성을 위한 코드
    descs = {}
    descs_avg = {}
    descs_mid = {}
    for name, img_path_list in img_paths.items():
        count = 0
        descs[name] = []
        for img_path in img_path_list:
            img_bgr = cv2.imread(img_path)
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            _, img_shapes, _, face_num = find_faces(img_rgb)

            # 얼굴을 못찾았을 때
            if face_num == 0:
                count += 1
                print(name, count, 'Face Detect Fail')
                continue
            elif face_num != 1:
                count += 1
                print(name, count, 'Too Many Faces')
                continue
            descs[name].append(encode_face(img_rgb, img_shapes)[0])
            count += 1
            print(name, count, 'finish')

    for name_descs, vector_list_descs in descs.items():
        descs_avg[name_descs] = sum(descs[name_descs]) / len(vector_list_descs)
        descs_mid[name_descs] = np.median(descs[name_descs], axis=0)

    file = open('model.pickle', 'wb')
    pickle.dump(descs, file)
    file.close()

    file_avg = open('model_avg.pickle', 'wb')
    pickle.dump(descs_avg, file_avg)
    file_avg.close()

    file_mid = open('model_mid.pickle', 'wb')
    pickle.dump(descs_mid, file_mid)
    file_mid.close()


def execute(classfier_desc, img_path):
    #테스트할 사진 인코딩
    img_bgr = cv2.imread(img_path)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    rects, shapes, _, face_num = find_faces(img_rgb)

    if face_num == 0:
        print("Face Detect Fail")
        return

    descriptors = encode_face(img_rgb, shapes)

    fig, ax = plt.subplots(1, figsize=(20, 20))
    ax.imshow(img_rgb)

    tag = ''
    for i, desc in enumerate(descriptors):
        out_name = ''
        pre_dist = float(9999999999)
        found = False
        for name, saved_descs in classfier_desc.items():
            #print(name)
            #print()
            for saved_desc in saved_descs:
                dist = np.linalg.norm([desc] - saved_desc, axis=1)
                #하한 값 설정
                if dist < 0.5:#0.6:
                    found = True
                    if out_name == '':      # 처음발견
                        #print(out_name, name, dist, pre_dist)
                        out_name = name
                        pre_dist = dist

                    elif pre_dist > dist:
                        #print(name, out_name, pre_dist, dist)
                        pre_dist = dist
                        if out_name != name:
                            #print(name, out_name)
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
                                     rects[i][1][1]-rects[i][0][1],
                                     rects[i][1][0]-rects[i][0][0],
                                     linewidth=2, edgecolor='r', facecolor='none')
            ax.add_patch(rect)

    if tag != '':
        folder = img_path.split('/')[:-1]
        file_name = img_path.split('/')[-1]
        folder = '/'.join(folder)
        print(folder)
        print(file_name)
        print(tag)
        os.rename(img_path, folder+'/'+'TAG_'+tag+'_'+file_name)

test_mode = 0
if test_mode == 0:          #분류기 생성
    create_classifier()

elif test_mode == 1:        #분류 실행
    #분류기 설정
    file = open('model.pickle', 'rb')
    descs = pickle.load(file)
    file.close()

    #file_avg = open('model_avg.pickle', 'rb')
    #descs_avg = pickle.load(file_avg)
    #file_avg.close()

    path_dir = u'C:/Users/User2/Desktop/Capstone1/test'
    file_list = os.listdir(path_dir)
    print(file_list)
    img_list = [file for file in file_list if 'jpg' in file or 'jpeg' in file or 'JPEG' in file or 'JPG' in file or
                'png' in file or 'PNG' in file]

    for img_file_name in img_list:
        execute(descs, path_dir+'/'+img_file_name)
        plt.show()



