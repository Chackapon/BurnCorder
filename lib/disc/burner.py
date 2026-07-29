from lib.file.discinstance import DiscInstance
from lib.disc.tray import DiscTrayBase
from lib.misc.configs import config





def burn_iteration(project: DiscInstance, tray: DiscTrayBase):
    ### BURN LOOP
    # Step 1: wait for a CD
    print("@ Waiting for CD...")
    tray.wait_for_cd()
    print("@ Detected CD...")

    # Step 2: check if empty; if full but RW, erase, if full CDR - eject
    if not tray.is_blank():

        print("@ Inserted CD is not blank, erasing...")
        if tray.is_erasable():
            tray.erase_cd()
            tray.wait_for_cd()
            assert tray.is_blank()

        else:
            print(f"! Error: CD is full and not erasable")
            tray.eject_cd()

    # Step 3: burn project
    print("@ Initiating burn...")
    project.burn_cd()
    # TODO wrap cdrdao output so it's less text, same for cdrecord but MORE text

    # Step 4: wait for the process to end idk

    # Step 5: verify burned CD
    try:
        tray.wait_for_cd()
        # project.verify_cd(tray)
        tray.verify_cd(project)
        print("@ Successfully verified burn")
    except RuntimeError as e:
        print(f"! Burn verification failed, reason: {e}")
    # TODO fix this, it tries to call drutil status too soon

    # Step 6: eject CD
    print("@ Finished, ejecting...")

    tray.eject_cd()


if __name__ == "__main__":
    pass

