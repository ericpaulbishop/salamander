#!/bin/bash
qemu -net nic,vlan=1 -net user,vlan=1 -cdrom downloaded/ubuntu-9.10-desktop-i386.iso -hda ../imgs/a.img -hdb ../imgs/b.img -hdc ../imgs/c.img -hdd ../imgs/d.img -boot d -m 512
