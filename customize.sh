#!/bin/bash

iso_file="$1"
iso_out="$2"


#cleanup
rm -rf "$iso_out" squashfs-root extract-iso

if [ ! -d "downloaded" ] ; then
	rm -rf downloaded
	mkdir downloaded
	chmod 777 downloaded
fi


#download iso if we don't have it
if [ ! -e "downloaded/$iso_file" ] ; then
	if [ -e "../$iso_file" ] ; then
		cp -r "../$iso_file" "downloaded/$iso_file"
	else
		cd downloaded
		wget "http://ubuntu.media.mit.edu/ubuntu-releases/releases/9.10/$iso_file"
		cd ..
	fi
fi


#unmount/remove any of the dirs we're going to be using if they already exist
umount iso >/dev/null 2>&1
rm -rf iso >/dev/null 2>&1


#mount iso
mkdir iso >/dev/null 2>&1
mount "downloaded/$iso_file" ./iso  -t iso9660 -o loop=/dev/loop1 >/dev/null 2>&1
iso_contents=$(ls iso 2>/dev/null)
if [ -z "$iso_contents" ] ; then
	echo "ERROR: Cannot mount iso image.  Make sure you have root priveledges and try again."
	rmdir iso >/dev/null 2>/dev/null
	exit
fi


#copy cd contents
rm -rf extract-iso
mkdir extract-iso
rsync --exclude=/casper/filesystem.squashfs -a iso/ extract-iso


#extract file system & unmount iso
rm -rf squashfs-root
unsquashfs iso/casper/filesystem.squashfs
umount iso
rm -rf iso


#copy new ubiquity scripts to new root
cp -rp ubiquity-lib/* squashfs-root/usr/lib/ubiquity/
cp -rp ubiquity-share/* squashfs-root/usr/share/ubiquity/
cp -rp bin/* squashfs-root/bin/

#add new debconf variables
cat debconf_additions/config.dat.add >> squashfs-root/var/cache/debconf/config.dat
cat debconf_additions/templates.dat.add >> squashfs-root/var/cache/debconf/templates.dat


#create script to add/remove desired packages by chrooting to file system
rm -rf chroot_run_commands.sh
echo 'mount -t proc none /proc' >> chroot_run_commands.sh
echo 'mount -t sysfs none /sys' >> chroot_run_commands.sh
echo 'mount -t devpts none /dev/pts' >> chroot_run_commands.sh
echo 'export HOME=/root'  >> chroot_run_commands.sh
echo 'export LC_ALL=C' >> chroot_run_commands.sh
echo 'dbus-uuidgen >/var/lib/dbus/machine-id' >> chroot_run_commands.sh

echo 'apt-get update' >> chroot_run_commands.sh
echo 'apt-get install -y vim-gnome' >> chroot_run_commands.sh
echo 'apt-get install -y xfsprogs' >> chroot_run_commands.sh
echo 'aptitude install --without-recommends -y mdadm' >> chroot_run_commands.sh
echo 'apt-get remove -y openoffice.org-thesaurus-en-au' >> chroot_run_commands.sh
echo 'apt-get remove -y language-pack-gnome-pt-base' >> chroot_run_commands.sh

echo 'aptitude clean' >> chroot_run_commands.sh
echo 'rm -rf /tmp/* ~/.bash_history' >> chroot_run_commands.sh
echo 'rm /var/lib/dbus/machine-id' >> chroot_run_commands.sh
echo 'umount /sys' >> chroot_run_commands.sh
echo 'umount /dev/pts' >> chroot_run_commands.sh
echo 'umount -lf /proc' >> chroot_run_commands.sh


#chroot and run update script
mv squashfs-root/etc/resolv.conf squashfs-root/etc/resolv.conf.bak 2>/dev/null
mv squashfs-root/etc/hosts squashfs-root/etc/hosts.bak 2>/dev/null
cp /etc/resolv.conf squashfs-root/etc/resolv.conf 2>/dev/null
cp /etc/hosts squashfs-root/etc/hosts 2>/dev/null

mv chroot_run_commands.sh squashfs-root 2>/dev/null
chroot squashfs-root /bin/sh chroot_run_commands.sh 2>/dev/null
rm squashfs-root/chroot_run_commands.sh 2>/dev/null

rm -rf squashfs-root/etc/resolv.conf
rm -rf squashfs-root/etc/hosts
mv squashfs-root/etc/resolv.conf.bak squashfs-root/etc/resolv.conf 2>/dev/null
mv squashfs-root/etc/hosts.bak squashfs-root/etc/hosts.conf 2>/dev/null
rm -rf squashfs-root/etc/mdadm


#copy scripts, preseed files and text.cfg to new iso directory
cp -r scripts extract-iso/
cp preseed/* extract-iso/preseed/
cp isolinux/* extract-iso/isolinux/


#build new cd image
chmod +w extract-iso/casper/filesystem.manifest
chroot squashfs-root dpkg-query -W --showformat='${Package} ${Version}\n' > extract-iso/casper/filesystem.manifest
cp extract-iso/casper/filesystem.manifest extract-iso/casper/filesystem.manifest-desktop
sed -i '/ubiquity/d' extract-iso/casper/filesystem.manifest-desktop
sed -i '/casper/d' extract-iso/casper/filesystem.manifest-desktop
rm -rf extract-iso/casper/filesystem.squashfs
mksquashfs squashfs-root extract-iso/casper/filesystem.squashfs
cd extract-iso
rm md5sum.txt
find -type f -print0 | sudo xargs -0 md5sum | grep -v isolinux/boot.cat | sudo tee md5sum.txt

mkisofs -D -r -V "salamander" -cache-inodes -J -l -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o "../$iso_out" .
