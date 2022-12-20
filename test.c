#include<stdio.h>
#include<stdlib.h>

typedef struct _queue
{
    int* A;
    int next_index;
}* queue;

queue make_queue(){
    queue Q;
    Q = malloc(sizeof(Q[0]));
    Q->A = (int*)malloc(sizeof(int));
    Q->next_index = 0;
}

void enqueue(queue Q, int x){
    if(sizeof(Q)/sizeof(int) == Q->next_index){
        int* B;
        B = malloc(sizeof(Q)*2);
        for(int i=0;i<sizeof(Q)/sizeof(int);i++){
            B[i] = Q->A[i];
        }
        Q->A = B;
    }
    Q->A[Q->next_index] = x;
    Q->next_index += 1;
}

int dequeue(queue Q){
    if(Q->next_index == 0){
        printf("MYERROR: Don't dequeue too much.");
        return 0;
    }
    Q->A = Q->A + 1;
    Q->next_index -=1;
    return *(Q->A - 1);
}

int main(){
    queue Q;
    int x;
    Q = make_queue();
    for(int i=0;i<4;i++){
        enqueue(Q, i);
    }
    for(int i=0;i<4;i++){
        x = dequeue(Q);
        printf("%d\n", x);
    }
    for(int i=0;i<4;i++){
        enqueue(Q, i);
    }
    for(int i=0;i<4;i++){
        x = dequeue(Q);
        printf("%d\n", x);
    }
    return 0;
}