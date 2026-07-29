import os
import plistlib
import subprocess




# TODO: replace with DrUtilProcess.dev_disk
def get_optical_drives_disk():
    result = []

    diskutil_output = subprocess.check_output(["diskutil", "list", "-plist"])
    disks_list = plistlib.loads(diskutil_output)["WholeDisks"]
    for disk in disks_list:
        disk_info = subprocess.check_output(["diskutil", "info", "/dev/"+disk])
        if b'Optical' in disk_info:
            result.append( disk )

    return result

# TODO: maybe replace with DrUtilProcess.dev_disk (though it's unused anyway)
def get_current_cd_disk() -> bytes:
    output = subprocess.check_output(["drutil", "status"])
    idx = output.split().index(b'Name:') + 1
    return output.split()[idx]

#====================================
def get_optical_drives_bus():
    result = []

    # output = subprocess.check_output(["cdrecord", "-scanbus"], stderr=subprocess.DEVNULL).decode("utf-8").splitlines()
    output = call_cdrecord("-scanbus").decode("utf-8").splitlines()
    start_idx = output.index( 'scsibus1:' )
    for line in output[start_idx+1:]:
        if "CD-ROM" in line:
            result.append( line.split()[0] )

    return result

# TODO consider moving to DiskTray class
def unmount_optical_vols():
    volumes = os.listdir("/Volumes/")

    print("Unmounting all optical media volumes...")
    for volume in volumes:
        if not volume.startswith("."):
            volume_info = subprocess.check_output(["diskutil", "info", "-plist", f"/Volumes/{volume}"])
            if "OpticalDeviceType" in plistlib.loads(volume_info).keys():
                print("* Unmounting " + volume)

                print("> ", end="")
                subprocess.run(["hdiutil", "unmount", f"/Volumes/{volume}"])


def call_cdrecord( *args ):
    command = ["cdrecord"] + list(args)
    # unmountOpticalVols()
    # return subprocess.check_output(command, stderr=subprocess.DEVNULL)
    # print(args)
    # command = ["cdrecord"] + list(args)
    result = b'err'
    try:
        result = subprocess.check_output(command, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        if e.returncode == 255:
            unmount_optical_vols()
            result = call_cdrecord(*args)

    return result

def msinfo():
    return call_cdrecord("-msinfo")

if __name__ == "__main__":
    pass
