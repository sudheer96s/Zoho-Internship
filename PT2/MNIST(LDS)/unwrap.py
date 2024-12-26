import pickle
import numpy as np
import matplotlib.pyplot as plt

# Load the pickle file with the correct encoding
with open('mnist.pkl', 'rb') as file:
    mnist_data = pickle.load(file, encoding='latin1')  # Specify encoding

# Inspect the structure of the data
print(f"Type: {type(mnist_data)}")
print(f"Length of mnist_data: {len(mnist_data)}")

# If it is a tuple, print the types or structure of each element
for i, element in enumerate(mnist_data):
    print(f"Element {i}: {type(element)}")

# Assuming the tuple contains training, validation, and test datasets
train_data, val_data, test_data = mnist_data

# Unpack the training data
images, labels = train_data  # Adjust based on the inspected structure

# Convert to numpy arrays
images = np.array(images)
labels = np.array(labels)

print(f"Images shape: {images.shape}")
print(f"Labels shape: {labels.shape}")

# Visualize the first few images
for i in range(5):  # Show 5 images
    plt.imshow(images[i].reshape(28, 28), cmap='gray')  # Reshape if needed
    plt.title(f"Label: {labels[i]}")
    plt.axis('off')
    plt.show()
