

start_name = 70

import os

for webpage in os.listdir('./'):
	if os.path.isdir('./' + webpage):
		counter = 0
		for directory in os.listdir('./' + webpage + '/'):
			file_path = './' + webpage + '/' + directory + '/'
			os.rename(file_path, './' + webpage + '/' + str(start_name + counter))
			counter = counter + 1 
		
