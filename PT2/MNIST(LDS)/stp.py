import pickle

# Load the pickle file
with open('mnist.pkl', 'rb') as file:
    mnist_data = pickle.load(file, encoding='latin1')  # Use 'latin1' for compatibility

# Check the structure
print(f"Type of mnist_data: {type(mnist_data)}")

# If it's a tuple, check its length and types of elements
if isinstance(mnist_data, tuple):
    print(f"Number of elements in mnist_data: {len(mnist_data)}")
    for i, element in enumerate(mnist_data):
        print(f"Element {i} type: {type(element)}")
        if isinstance(element, tuple):
            print(f"  Sub-element {i} length: {len(element)}")
            for j, sub_element in enumerate(element):
                print(f"  Sub-element {j} type: {type(sub_element)}")
                if hasattr(sub_element, "shape"):
                    print(f"    Shape: {sub_element.shape}")
                else:
                    print(f"    Length: {len(sub_element)}")
