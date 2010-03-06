#!/bin/bash

iso=$( echo $(ls  | grep salamander64.*.iso  ) | awk ' { print $1 ; } ')
if [ -e "$iso" ] ; then 
	qemu-system-x86_64 -cdrom "$iso" -hda ../imgs/a.img -hdb ../imgs/b.img -hdc ../imgs/c.img  -boot d -m 512
fi
