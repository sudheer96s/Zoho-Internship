#include <iostream>
#include <fstream>
using namespace std;

int main() {
    ofstream outfile("example.txt");
    outfile << "Helloworld, File!" << endl;
    outfile.close();

    ifstream infile("example.txt");
    string data;
    infile >> data;
    cout << "Read from file: " << data << endl;

    infile.close();
    return 0;
}
