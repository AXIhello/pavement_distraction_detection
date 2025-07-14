import dlib
import numpy as np
import cv2
import base64
from scipy.spatial import distance as dist
import os

# 68点模型索引
LEFT_EYE = list(range(42, 48))
RIGHT_EYE = list(range(36, 42))
MOUTH = list(range(48, 68))
NOSE = list(range(27, 36))
JAW = list(range(0, 17))
LEFT_EYEBROW = list(range(22, 27))


CUR_DIR = os.path.dirname(os.path.abspath(__file__))
predictor_path = os.path.abspath(os.path.join(CUR_DIR, '..', '..', 'data', 'data_dlib', 'shape_predictor_68_face_landmarks.dat'))
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(predictor_path)


def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

def mouth_aspect_ratio(mouth):
    A = np.linalg.norm(mouth[2] - mouth[9])
    B = np.linalg.norm(mouth[4] - mouth[7])
    C = np.linalg.norm(mouth[0] - mouth[6])
    return (A + B) / (2.0 * C)

def nose_jaw_distance(nose, jaw):
    face_left1 = dist.euclidean(nose[0], jaw[0])
    face_right1 = dist.euclidean(nose[0], jaw[16])
    face_left2 = dist.euclidean(nose[3], jaw[2])
    face_right2 = dist.euclidean(nose[3], jaw[14])
    return (face_left1, face_right1, face_left2, face_right2)

def eyebrow_jaw_distance(leftEyebrow, jaw):
    eyebrow_left = dist.euclidean(leftEyebrow[2], jaw[0])
    eyebrow_right = dist.euclidean(leftEyebrow[2], jaw[16])
    left_right = dist.euclidean(jaw[0], jaw[16])
    return (eyebrow_left, eyebrow_right, left_right)

# 活体检测主函数

def liveness_check(base64_image, status):
    # 阈值
    EYE_AR_THRESH = 0.27
    EYE_AR_CONSEC_FRAMES = 2
    MAR_THRESH = 0.5

    # 状态初始化
    COUNTER_EYE = status.get('COUNTER_EYE', 0)
    TOTAL_EYE = status.get('TOTAL_EYE', 0)
    COUNTER_MOUTH = status.get('COUNTER_MOUTH', 0)
    TOTAL_MOUTH = status.get('TOTAL_MOUTH', 0)
    distance_left = status.get('distance_left', 0)
    distance_right = status.get('distance_right', 0)
    TOTAL_FACE = status.get('TOTAL_FACE', 0)
    nod_flag = status.get('nod_flag', 0)
    TOTAL_NOD = status.get('TOTAL_NOD', 0)

    # 解码图片
    header, encoded = base64_image.split(',')
    nparr = np.frombuffer(base64.b64decode(encoded), np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    rects = detector(gray, 0)
    for rect in rects:
        shape = predictor(gray, rect)
        shape = np.array([[p.x, p.y] for p in shape.parts()])

        leftEye = shape[LEFT_EYE]
        rightEye = shape[RIGHT_EYE]
        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)
        Mouth = shape[MOUTH]
        mouthMAR = mouth_aspect_ratio(Mouth)
        nose = shape[NOSE]
        jaw = shape[JAW]
        NOSE_JAW_Distance = nose_jaw_distance(nose, jaw)
        leftEyebrow = shape[LEFT_EYEBROW]
        Eyebrow_JAW_Distance = eyebrow_jaw_distance(leftEyebrow, jaw)

        ear = (leftEAR + rightEAR) / 2.0
        mar = mouthMAR
        face_left1, face_right1, face_left2, face_right2 = NOSE_JAW_Distance
        eyebrow_left, eyebrow_right, left_right = Eyebrow_JAW_Distance

        # 眨眼
        if ear < EYE_AR_THRESH:
            COUNTER_EYE += 1
        else:
            if COUNTER_EYE >= EYE_AR_CONSEC_FRAMES:
                TOTAL_EYE += 1
            COUNTER_EYE = 0

        # 张嘴
        if mar > MAR_THRESH:
            COUNTER_MOUTH += 1
        else:
            if COUNTER_MOUTH != 0:
                TOTAL_MOUTH += 1
                COUNTER_MOUTH = 0

        # 摇头
        if face_left1 >= face_right1+2 and face_left2 >= face_right2+2:
            distance_left += 1
        if face_right1 >= face_left1+2 and face_right2 >= face_left2+2:
            distance_right += 1
        if distance_left != 0 and distance_right != 0:
            TOTAL_FACE += 1
            distance_right = 0
            distance_left = 0

        # 点头
        if eyebrow_left+eyebrow_right <= left_right+3:
            nod_flag += 1
        if nod_flag != 0 and eyebrow_left+eyebrow_right >= left_right+3:
            TOTAL_NOD += 1
            nod_flag = 0

    # 进度和提示
    progress = 0
    next_action = "请眨眼5次"
    if TOTAL_EYE < 5:
        progress = int(TOTAL_EYE / 5 * 25)
        next_action = f"请眨眼（已完成{TOTAL_EYE}/5）"
    elif TOTAL_MOUTH < 3:
        progress = 25 + int(TOTAL_MOUTH / 3 * 25)
        next_action = f"请张嘴（已完成{TOTAL_MOUTH}/3）"
    elif TOTAL_FACE < 2:
        progress = 50 + int(TOTAL_FACE / 2 * 25)
        next_action = f"请摇头（已完成{TOTAL_FACE}/2）"
    elif TOTAL_NOD < 2:
        progress = 75 + int(TOTAL_NOD / 2 * 25)
        next_action = f"请点头（已完成{TOTAL_NOD}/2）"
    else:
        progress = 100
        next_action = "活体检测通过"

    # 返回状态
    new_status = {
        'COUNTER_EYE': COUNTER_EYE,
        'TOTAL_EYE': TOTAL_EYE,
        'COUNTER_MOUTH': COUNTER_MOUTH,
        'TOTAL_MOUTH': TOTAL_MOUTH,
        'distance_left': distance_left,
        'distance_right': distance_right,
        'TOTAL_FACE': TOTAL_FACE,
        'nod_flag': nod_flag,
        'TOTAL_NOD': TOTAL_NOD
    }
    return progress, next_action, new_status