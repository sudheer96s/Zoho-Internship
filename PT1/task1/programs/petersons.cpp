#include <iostream>
#include <vector>
#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <sys/time.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <sys/wait.h>

#define BSIZE 8
#define PWT 2
#define CWT 10
#define RT 10

int shmid1, shmid2, shmid3, shmid4;
key_t k1 = 5491, k2 = 5812, k3 = 4327, k4 = 3213;

bool* SHM1;
int* SHM2;
int* SHM3;

void initializeBuffer(int* buf, int size) {
    for (int i = 0; i < size; ++i) {
        buf[i] = 0;
    }
}

int myrand(int n) {
    static int initialized = 0;
    if (!initialized) {
        srand(static_cast<unsigned>(time(nullptr)));
        initialized = 1;
    }
    return (rand() % n + 1);
}

void cleanup() {
    shmdt(SHM1);
    shmdt(SHM2);
    shmdt(SHM3);
    shmctl(shmid1, IPC_RMID, nullptr);
    shmctl(shmid2, IPC_RMID, nullptr);
    shmctl(shmid3, IPC_RMID, nullptr);
    shmctl(shmid4, IPC_RMID, nullptr);
}

int main() {
    shmid1 = shmget(k1, sizeof(bool) * 2, IPC_CREAT | 0660);
    shmid2 = shmget(k2, sizeof(int) * 1, IPC_CREAT | 0660);
    shmid3 = shmget(k3, sizeof(int) * BSIZE, IPC_CREAT | 0660);
    shmid4 = shmget(k4, sizeof(int) * 1, IPC_CREAT | 0660);

    if (shmid1 < 0 || shmid2 < 0 || shmid3 < 0 || shmid4 < 0) {
        perror("Main shmget error: ");
        exit(1);
    }

    SHM3 = static_cast<int*>(shmat(shmid3, nullptr, 0));
    initializeBuffer(SHM3, BSIZE);

    struct timeval t;
    gettimeofday(&t, nullptr);
    time_t t1 = t.tv_sec;

    int* state = static_cast<int*>(shmat(shmid4, nullptr, 0));
    *state = 1;

    int i = 0; // Consumer
    int j = 1; // Producer

    if (fork() == 0) // Producer code
    {
        SHM1 = static_cast<bool*>(shmat(shmid1, nullptr, 0));
        SHM2 = static_cast<int*>(shmat(shmid2, nullptr, 0));
        SHM3 = static_cast<int*>(shmat(shmid3, nullptr, 0));

        if (SHM1 == nullptr || SHM2 == nullptr || SHM3 == nullptr) {
            perror("Producer shmat error: ");
            exit(1);
        }

        bool* flag = SHM1;
        int* turn = SHM2;
        int* buf = SHM3;
        int index = 0;

        while (*state == 1) {
            flag[j] = true;
            printf("Producer is ready now.\n\n");
            *turn = i;

            while (flag[i] == true && *turn == i) {
                usleep(100); // Sleep to reduce CPU usage during busy wait
            }

            // Critical Section Begin
            index = 0;
            while (index < BSIZE) {
                if (buf[index] == 0) {
                    int tempo = myrand(BSIZE * 3);
                    printf("Job %d has been produced\n", tempo);
                    buf[index] = tempo;
                    break;
                }
                index++;
            }

            if (index == BSIZE)
                printf("Buffer is full, nothing can be produced!!!\n");

            printf("Buffer: ");
            index = 0;
            while (index < BSIZE)
                printf("%d ", buf[index++]);
            printf("\n");
            // Critical Section End

            flag[j] = false;
            if (*state == 0)
                break;

            int wait_time = myrand(PWT);
            printf("Producer will wait for %d seconds\n\n", wait_time);
            sleep(wait_time);
        }

        exit(0);
    }

    if (fork() == 0) // Consumer code
    {
        SHM1 = static_cast<bool*>(shmat(shmid1, nullptr, 0));
        SHM2 = static_cast<int*>(shmat(shmid2, nullptr, 0));
        SHM3 = static_cast<int*>(shmat(shmid3, nullptr, 0));

        if (SHM1 == nullptr || SHM2 == nullptr || SHM3 == nullptr) {
            perror("Consumer shmat error:");
            exit(1);
        }

        bool* flag = SHM1;
        int* turn = SHM2;
        int* buf = SHM3;
        int index = 0;
        flag[i] = false;

        while (*state == 1) {
            flag[i] = true;
            printf("Consumer is ready now.\n\n");
            *turn = j;

            while (flag[j] == true && *turn == j) {
                usleep(100); // Sleep to reduce CPU usage during busy wait
            }

            // Critical Section Begin
            if (buf[0] != 0) {
                printf("Job %d has been consumed\n", buf[0]);
                index = 1;
                while (index < BSIZE) {
                    buf[index - 1] = buf[index];
                    index++;
                }
                buf[index - 1] = 0;
            } else
                printf("Buffer is empty, nothing can be consumed!!!\n");

            printf("Buffer: ");
            index = 0;
            while (index < BSIZE)
                printf("%d ", buf[index++]);
            printf("\n");
            // Critical Section End

            flag[i] = false;
            if (*state == 0)
                break;

            int wait_time = myrand(CWT);
            printf("Consumer will sleep for %d seconds\n\n", wait_time);
            sleep(wait_time);
        }

        exit(0);
    }

    // Parent process will now wait for RT seconds before causing the child to terminate
    while (1) {
        gettimeofday(&t, nullptr);
        time_t t2 = t.tv_sec;
        if (t2 - t1 > RT) {
            *state = 0;
            break;
        }
        usleep(100000); // Sleep to avoid busy-waiting in the parent process
    }

    // Waiting for both processes to exit
    wait(nullptr);
    wait(nullptr);

    cleanup();
    printf("The clock ran out.\n");

    return 0;
}
