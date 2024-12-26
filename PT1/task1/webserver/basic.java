public class MemoryDemo {

    // A simple class to represent an object in the heap
    static class Person {
        String name;
        int age;

        Person(String name, int age) {
            this.name = name;
            this.age = age;
        }

        void displayInfo() {
            System.out.println("Name: " + name + ", Age: " + age);
        }
    }

    public static void main(String[] args) {
        // Stack memory: local variables
        int number = 10;  // Primitive type stored directly in stack

        // Creating objects in heap memory
        Person person1 = new Person("Alice", 30); // 'person1' is a reference to the Person object in heap
        Person person2 = new Person("Bob", 25);   // 'person2' is another reference to a different Person object

        // Displaying information
        System.out.println("Initial values:");
        person1.displayInfo();
        person2.displayInfo();

        // Changing the reference
        person1 = person2; // 'person1' now refers to the same object as 'person2'

        System.out.println("\nAfter changing reference:");
        person1.displayInfo(); // This will now display the information of 'person2'

        // Changing the object data through one reference
        person1.name = "Charlie"; // Changes the name in the object both 'person1' and 'person2' refer to

        System.out.println("\nAfter modifying the object through one reference:");
        person1.displayInfo();
        person2.displayInfo();

        // Garbage collection will clean up the unused "Alice" object, as it's no longer referenced
    }
}
