import os

_DESCARGAS = "/home/ismael/Descargas/"

for vpn in os.listdir(_DESCARGAS):
    if os.path.isdir(_DESCARGAS + vpn):
        for webpage in os.listdir(_DESCARGAS + vpn + os.path.sep):
            webdir = _DESCARGAS + vpn + os.path.sep + webpage
            if os.path.isdir(webdir):
                for run in os.listdir(webdir):
                    rundir = webdir + os.path.sep + run
                    if os.path.isdir(rundir):
                        if not (len(os.listdir(rundir)) >= 1):
                            # rundir empty, delete.
                            print("Removing empty rundir %s" % rundir)
                            os.rmdir(rundir)
                    else:
                        # trashable files
                        print("Removing trashfile %s" % rundir)
                        os.remove(rundir)
            else:
                # trashable files
                print("Removing trashfile %s" % webdir)
                os.remove(webdir)
