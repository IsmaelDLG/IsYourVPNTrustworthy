import os

ROOT_DIR = "F:\\Descargas\\"

start_run = 1000

for extension in os.listdir(ROOT_DIR):
    if os.path.isdir(os.path.join(ROOT_DIR, extension)):
        ext_dir = os.path.join(ROOT_DIR, extension)
        for webpage in os.listdir(ext_dir):
            if os.path.isdir(os.path.join(ext_dir, webpage)):
                web_dir = os.path.join(ext_dir, webpage)
                for run in os.listdir(web_dir):
                    if os.path.isdir(os.path.join(web_dir, run)):
                        run_dir = os.path.join(web_dir, run)
                        os.rename(run_dir, os.path.join(web_dir, str(start_run)))
                        start_run += 1
