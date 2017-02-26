#!/usr/bin/python3

from shutil import copytree, copy2
import logging
from logging.handlers import RotatingFileHandler
from os import path, listdir, mkdir, walk

def path_without_root(path):
	pos = path.find('/')  # attention: conpatibility on win!
	path = path[pos+1:]
	return path

class Safer(object):
	"""Manage the creation of the duplicate directory of the folder placed under supervision.

	Filename, folder, path to folder and extension can be exclude.

	"""
	# Destination folder: make in __init__
	# Delicate folders in destination: make in get_destination, call in __init__
	# Folder of version and delicate folder in version folder: make in save

	def __init__(self, delicate_dirs=list(), destination=str(), config=dict()):
		""""delicate_dirs: list of different directories placed under supervision."""
		super(Safer, self).__init__()
		# Logging
		self.logger = logging.getLogger()
		self.logger.setLevel(logging.DEBUG)
		# Log in a file
		file_handler = RotatingFileHandler('activity.log', 'a', 1000000, 1)
		file_handler.setLevel(logging.DEBUG)
		formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
		file_handler.setFormatter(formatter)
		self.logger.addHandler(file_handler)
		# Log in the console
		steam_handler = logging.StreamHandler()
		steam_handler.setLevel(logging.DEBUG)
		self.logger.addHandler(steam_handler)

		# Set destination directories
		self.delicate_dirs = delicate_dirs
		self.destination = destination
		# Make destination directories
		if not path.exists(self.destination):
			self.logger.info('mkdir dst: ' + self.destination)
			mkdir(self.destination)  # e.g. safe_docs
		self.safe_dirs = self.get_destination(delicate_dirs)

		# Config
		self.exclude_filename = []
		self.exclude_dirname = []  # All folder-name in this list are exclude
		self.exclude_dirpath = []  # Specific path to a folder to exclude
		self.exclude_ext = []
		# TODO: get config from a file (cammand line), or give them in arg (interface)

	def get_destination(self, delicate_dirs):
		"""Create a dict with folder under supervision as key and the path to their safe destination with their version.

		Two path for each folder: copy with filter and without.

		"""
		safe_dirs = dict()
		for dirname in delicate_dirs:
			# Make safe directory for each delicate folder
			root_destination = path.join(self.destination, dirname)  # e.g. delicate_dir/my_work
			if not path.exists(root_destination):
				self.logger.info('mkdir rt dst: ' + root_destination)
				mkdir(root_destination)  # e.g. safe_docs/my_work
			# Get versions
			version_copy = self.get_version(root_destination, 'COPY')
			version_filter = self.get_version(root_destination)
			# Add the safe directories
			dst_copy = path.join(self.destination, dirname, dirname + 'COPY-' + version_copy)
			dst_filter = path.join(self.destination, dirname, dirname + 'FILTER-' + version_filter)
			destination = {'COPY': dst_copy, 'FILTER': dst_filter}
			safe_dirs[dirname] = destination
		return safe_dirs

	def get_version(self, root_destination, _type='FILTER'):
		"""Return the current version of the given safe directory.

		_type is 'FILTER' or 'COPY'

		"""
		list_version = list()
		for directory_version in listdir(root_destination):
			dir_splited = directory_version.split(_type + '-')
			if len(dir_splited) == 2:
				list_version.append(int(dir_splited[1]))

		if list_version == []:
			version = '1'
		else:
			version = str(max(list_version) + 1)  # Take the last version + 1
		return version

	def save(self, _filter=False):
		"""Save all folder under supervision.

		It create the directories requires.
		If _filter is False (default), it don't save the files that don't match with the exclusion rules.

		"""
		self.logger.info('Start saving')
		if _filter:
			for dirname, safe_path in self.safe_dirs.items():
				self.logger.info('mkdir sf pt: ' + safe_path['FILTER'])
				mkdir(safe_path['FILTER'])  # e.g. safe_docs/my_work/my_workV--n
				to_save, dir_to_make = self.get_to_save(dirname)

				for dirname in dir_to_make:
					dirname = path_without_root(dirname)
					self.logger.info('mkdir sf pt drnm: ' + path.join(safe_path['FILTER'], dirname))
					mkdir(path.join(safe_path['FILTER'], dirname))  # e.g. safe_docs/my_work/my_workV--n/folder
				self.save_files(to_save, safe_path)
		else:
			self.logger.info('Save all the entire folder.')
			for dirname, safe_path in self.safe_dirs.items():
				self.logger.info('Saving ' + dirname)
				copytree(dirname, safe_path['COPY'])
		self.logger.info('Done')

	def get_to_save(self, directory):
		"""Return a list of file to save from a the given delicate directory, using walk.

		It make this list depending on exclusion rules.

		"""
		list_files = list()  # List of relatif path to each file
		dir_to_make = list()  # List of directory to make in the safe root directory
		for dirpath, dirnames, filenames in walk(directory):  # walk() return a generator
			# dirpath = directory, for the first time
			# dirpath = subdirs of directory
			# Exclude a directory name
			if path.basename(dirpath) in self.exclude_dirname:
				break
			dirname = path_without_root(dirpath)
			# Exclude a path
			if dirname not in self.exclude_dirpath:
				if path.basename(dirpath) != directory:
					dir_to_make.append(dirpath)
				for filename in filenames:
					# Find the extension
					ext = path.splitext(filename)[1][1:]
					if filename not in self.exclude_filename and ext not in self.exclude_ext:
						list_files.append(path.join(dirpath, filename))
		return list_files, dir_to_make

	def save_files(self, to_save, safe_path):
		for filename in to_save:
			dst = path.join(safe_path['FILTER'], path_without_root(filename))
			self.logger.info('coping: '+ dst)
			copy2(filename, dst)