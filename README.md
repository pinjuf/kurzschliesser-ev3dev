# kurzschliesser-ev3dev

## Getting started

 1) Follow the instructions on [ev3dev.org](https://www.ev3dev.org/docs/tutorials/connecting-to-the-internet-via-usb/)
 2) Mount the brick's filesystem: `mkdir $mountpoint; sshfs robot@ev3dev.local: $mountpoint`
    > You will be asked a passwd, the default on ev3dev is `maker`
    >
    > `sshfs` requires the FUSE linux kernel module. It will not work on WSL 1 etc. , which doesn't provide an actual kernel.
    > 
    > To unmount, use `fusermount -uz $mountpoint`
 3) CD into the Brick's FS: `cd $mountpoint`
 4) Clone this repo if not already done: `git clone https://github.com/pinjuf/kurzschliesser-ev3dev`
 5) You can now execute the `main.py` script using either Brickman (recommended) or `ssh robot@ev3dev.local ./kurzschliesser-ev3dev/main.py`
    > The screen on ev3dev is usually reserved for Brickman's TTY. If you want to run from SSH and have access to the terminal, use `sudo chvt $N` and optionally `sudo conspy` to bind your PTS to the screen. You can then revert back to the Brickman TTY.
