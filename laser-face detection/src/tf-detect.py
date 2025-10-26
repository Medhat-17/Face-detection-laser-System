# python/detect_tf.py
import tensorflow as tf
import numpy as np
import cv2
import argparse
import json
import sys
from pathlib import Path

IMG_W = 320
IMG_H = 240

def load_model(path):
    return tf.keras.models.load_model(path)

def preprocess(img):
    img = cv2.resize(img, (IMG_W, IMG_H))
    img = img.astype('float32')/255.0
    return np.expand_dims(img, 0)

def detect_from_image(model, img):
    x = preprocess(img)
    prob, bbox = model.predict(x)
    p = float(prob[0,0])
    bx, by, bw, bh = map(float, bbox[0])
    # convert normalized center to pixel coords
    x_px = bx * IMG_W
    y_px = by * IMG_H
    w_px = bw * IMG_W
    h_px = bh * IMG_H
    if p > 0.5:
        return {'prob': p, 'x': x_px, 'y': y_px, 'w': w_px, 'h': h_px}
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='../tf/saved_model', help='path to model')
    parser.add_argument('--image', default=None, help='image path (if omitted use webcam)')
    parser.add_argument('--single', action='store_true', help='run single inference and print JSON (for orchestrator)')
    args = parser.parse_args()

    model = load_model(args.model)
    if args.image:
        img = cv2.imread(args.image)
        res = detect_from_image(model, img)
        if args.single:
            if res:
                print(json.dumps(res))
            else:
                print("NONE")
            return
        else:
            print(res)
            return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera", file=sys.stderr); return
    while True:
        ret, frame = cap.read()
        if not ret: break
        det = detect_from_image(model, frame)
        if det:
            x,y,w,h = int(det['x']), int(det['y']), int(det['w']), int(det['h'])
            cv2.rectangle(frame, (x-w//2,y-h//2),(x+w//2,y+h//2),(0,255,0),2)
            cv2.putText(frame, f"{det['prob']:.2f}", (x-20,y-25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255),2)
        cv2.imshow('det', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
