# tf/train_tf.py
import numpy as np
import cv2
import os
import random
from tensorflow import keras
from tensorflow.keras import layers

IMG_W = 320
IMG_H = 240

def synth_image(with_target=True):
    img = np.zeros((IMG_H, IMG_W, 3), dtype=np.uint8)
    # background noise
    img[:] = (random.randint(0,60), random.randint(0,60), random.randint(0,60))
    # draw random rectangles as clutter
    for _ in range(10):
        x1 = random.randint(0, IMG_W-1); y1 = random.randint(0, IMG_H-1)
        x2 = min(IMG_W-1, x1 + random.randint(5, 80)); y2 = min(IMG_H-1, y1 + random.randint(5,80))
        color = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
        cv2.rectangle(img, (x1,y1), (x2,y2), color, -1)
    if with_target:
        # draw a red circle target
        cx = random.randint(30, IMG_W-30)
        cy = random.randint(30, IMG_H-30)
        r = random.randint(8, 24)
        cv2.circle(img, (cx,cy), r, (0,0,255), -1)
        # return normalized bbox
        x = cx/IMG_W; y = cy/IMG_H; w = (2*r)/IMG_W; h = (2*r)/IMG_H
        return img, 1.0, np.array([x,y,w,h], dtype=np.float32)
    else:
        return img, 0.0, np.zeros(4, dtype=np.float32)

def build_model():
    inp = keras.Input(shape=(IMG_H, IMG_W, 3))
    x = layers.Rescaling(1./255)(inp)
    x = layers.Conv2D(16, 3, activation='relu')(x)
    x = layers.MaxPool2D()(x)
    x = layers.Conv2D(32, 3, activation='relu')(x)
    x = layers.MaxPool2D()(x)
    x = layers.Conv2D(64, 3, activation='relu')(x)
    x = layers.GlobalAveragePooling2D()(x)
    # classification head
    cls = layers.Dense(64, activation='relu')(x)
    cls = layers.Dense(1, activation='sigmoid', name='prob')(cls)
    # bbox head
    bbox = layers.Dense(64, activation='relu')(x)
    bbox = layers.Dense(4, activation='sigmoid', name='bbox')(bbox)
    model = keras.Model(inputs=inp, outputs=[cls, bbox])
    model.compile(optimizer='adam',
                  loss={'prob':'binary_crossentropy', 'bbox':'mse'},
                  loss_weights={'prob':1.0, 'bbox':10.0})
    return model

def generator(batch_size=16, positive_ratio=0.5):
    while True:
        imgs = np.zeros((batch_size, IMG_H, IMG_W, 3), dtype=np.float32)
        probs = np.zeros((batch_size,1), dtype=np.float32)
        bboxes = np.zeros((batch_size,4), dtype=np.float32)
        for i in range(batch_size):
            if random.random() < positive_ratio:
                img, p, bbox = synth_image(True)
            else:
                img, p, bbox = synth_image(False)
            imgs[i] = img
            probs[i,0] = p
            bboxes[i] = bbox
        yield imgs, {'prob':probs, 'bbox':bboxes}

def train(out_dir='saved_model', epochs=6):
    model = build_model()
    steps_per_epoch = 100
    model.fit(generator(), steps_per_epoch=steps_per_epoch, epochs=epochs, verbose=2)
    os.makedirs(out_dir, exist_ok=True)
    model.save(out_dir)
    print("Saved model to", out_dir)

if __name__ == '__main__':
    train()
