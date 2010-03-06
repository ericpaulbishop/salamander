#!/bin/bash
iso=$( echo $(ls  | grep salamander32.*.iso  ) | awk ' { print $1 ; } ')
if [ -e "$iso" ] ; then 
	qemu -net none  -cdrom "$iso" -hda ../imgs/a.img -hdb ../imgs/b.img -hdc ../imgs/c.img -boot d -m 512
fi
#qemu -net none  -cdrom salamander.iso -drive file=../imgs/a.img,if=scsi,bus=0,unit=1  -drive file=../imgs/b.img,if=scsi,bus=0,unit=2 -drive file=../imgs/c.img,if=scsi,bus=0,unit=3  -drive file=../imgs/b.img,if=scsi,bus=0,unit=4 -boot d -m 512

