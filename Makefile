all: salamander

salamander:
	sh customize.sh

clean:
	rm -rf salamander.iso squashfs-root extract-iso
