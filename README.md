# kurzschliesser-ev3dev

## Getting started

### Requirements

 - some version of Linux for the EV3 (preferably [ev3dev's Debian](https://www.ev3dev.org/downloads/))
 - git
 - a robot similar to `robo_V1.io` (BrickLink Studio file)

### Setting up and running

 1) Follow the instructions on [ev3dev.org](https://www.ev3dev.org/docs/tutorials/connecting-to-the-internet-via-usb/)
 2) Mount the brick's filesystem: `mkdir $mountpoint; sshfs -o idmap=user robot@ev3dev.local: $mountpoint`
    > You will be asked a passwd, the default on ev3dev is `maker`
    >
    > `sshfs` requires the FUSE linux kernel module. It will not work on WSL 1 etc., which doesn't provide an actual kernel.
    > 
    > To unmount, use `fusermount -uz $mountpoint`
 3) CD into the Brick's FS: `cd $mountpoint`
 4) Clone this repo if not already done: `git clone https://github.com/pinjuf/kurzschliesser-ev3dev`
 5) You can now execute the `main.py` script using either Brickman (recommended) or `ssh robot@ev3dev.local ./kurzschliesser-ev3dev/main.py`
    > The screen on ev3dev is usually reserved for Brickman's reserved TTY. If you want to run from SSH and have access to the terminal, use `sudo chvt $N` and optionally `sudo conspy` to bind your PTS to the screen. You can then revert back to the Brickman TTY.

## About some files

### `robo_V1.io`
This is a BrickLink Studio model file of our robot, the `Kabelstapler`. It's pretty much the best Lego modelling software, but it's proprietary and only has Windows builds (I truly am sorry). So if you're an absolute chad who uses Linux (we use Arch BTW), you will need to use Wine or a VM.
