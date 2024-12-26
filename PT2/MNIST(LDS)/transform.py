import numpy as np

import os
from PIL import Image
import pickle

def save_image_as_png(images,labels,output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for idx, (image, label) in enumerate(zip(images,labels)):
        image = image.reshape(28,28)
        image = np.uint8(image*255)
        img = Image.fromarray(image,mode = "L")
        img.save(os.path.join(output_dir,f"{label}_{idx}.png"))


def load_and_process_mnist(file_path):
    with open(file_path,'rb') as f:
        mnist_data = pickle.load(f,encoding='latin1')

    train_data , test_data, validate_data = mnist_data

    train_image , train_label = train_data
    test_image , test_label = test_data
    validate_image , validate_label = validate_data

    return train_image,train_label,test_image,test_label,validate_image,validate_label

file_path = "/home/manchik-pt7714/Documents/PT2/archive/mnist.pkl"

train_image,train_label,test_image,test_label,validate_image,validate_label = load_and_process_mnist(file_path)

save_image_as_png(train_image,train_label,'./train_images')
save_image_as_png(test_image,test_label,'./test_image')
save_image_as_png(validate_image,validate_label,'./validate_image')
print('done')
