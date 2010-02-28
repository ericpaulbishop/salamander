#!/bin/bash
qemu-system-x86_64 -cdrom salamander64.iso -hda ../imgs/a.img -hdb ../imgs/b.img -hdc ../imgs/c.img  -boot d -m 512
