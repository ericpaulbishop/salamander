#!/bin/bash

#cleanup
rm -rf salamander.iso 

#copy pressed to new iso directory
cp preseed/* extract-iso/preseed/

#copy scripts to new iso directory
cp -r scripts extract-iso/

#build new cd image
cd extract-iso
rm md5sum.txt
find -type f -print0 | sudo xargs -0 md5sum | grep -v isolinux/boot.cat | sudo tee md5sum.txt

mkisofs -D -r -V "salamander" -cache-inodes -J -l -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o ../salamander.iso .
