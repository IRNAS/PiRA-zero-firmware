"""
azure_images.py

It is a module that controls the uploading of the image/s

ENV VARS:
    - AZURE_ACCOUNT_NAME
    - AZURE_ACCOUNT_KEY
    - AZURE_CONTAINER_NAME

Tutorials: https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python
"""

from __future__ import print_function

import os
import time
import sys
from datetime import datetime

from azure.storage.blob import BlockBlobService, PublicAccess

# a dummy file to upload
full_path_to_file = "/usr/src/app/docs/logo-irnas.png"

class Module(object):
    def __init__(self, boot):
        """
        Inits the Azure method for PiRa
        """
        self._boot = boot
        self._enabled = False
        
        self.ACCOUNT_NAME = os.environ.get('AZURE_ACCOUNT_NAME', '')                    # get azure account name from env var
        self.ACCOUNT_KEY = os.environ.get('AZURE_ACCOUNT_KEY','')                       # get azure account key from env var
        self.container_name = os.environ.get('AZURE_CONTAINER_NAME', 'ImageExample')    # get container name, default is ImageExample

        # DEBUG
        #print(self.ACCOUNT_NAME)
        #print(self.ACCOUNT_KEY)
        #print(self.container_name)

        try:
            
            # create object for the servise
            self.block_blob_service = BlockBlobService(account_name=self.ACCOUNT_NAME, account_key=self.ACCOUNT_KEY)

            # create our container
            self.create_container()

            # Set the permission so the blobs are public.
            if self.block_blob_service.set_container_acl(self.container_name, public_access=PublicAccess.Container) is None:
                print("Soemthing went from when setting the container")
                return

            # it is set to True -> all okay
            self._enabled = True
        except Exception as e:
            print("AZURE ERROR: {}".format(e))
            self._enabled = False

    def create_container(self):
        """
        Inits the container under self.container_name name
        """
        try:
            self.block_blob_service.create_container(self.container_name)
        except Exception as e:
            print("Something went wrong when creating container, error: {}".format(e))
            return
    
    def upload_via_path(self,_path):
        """
        It uploads the file to the self.container_name via _path
        """
        
        try:
            # splitting the path and filename
            path, filename = os.path.split(_path)
            
            # checking if it is valid (will give exception if not valid)
            file = open(_path, 'r')
            file.close()
  
            # debug
            print("Uplading to storage file: {} {}".format(_path, filename))

            # uploading it
            if self.block_blob_service.create_blob_from_path(self.container_name, filename, _path) is None:
                print("Something went wrong on upload!")
                return

            # debug
            print("Uploaded: {}".format(filename))

        except Exception as e:
            print("AZURE ERROR: {}".format(e))

    def delete_via_container(self, _container_name):
        """
        Deletes the container under _container_name (self.container_name)
        """
        try:
            if self.block_blob_service.delete_container(_container_name) is False:
                print("Something went wrong on delete!")
                return
            print("Deleted: {}".format(_container_name))
        
        except Exception as e:
            print("AZURE ERROR: {}".format(e))

    def process(self, modules):
        """
        Process for the azure module
        """
        print("AZURE process | Inited: {}".format(self._enabled))
        if self._enabled is False:
            return
        
        try:
            #self.create_container() 
            #self.upload_via_path(full_path_to_file)
            #time.sleep(60)
            #self.delete_via_container(self.container_name)
            pass
        except Exception as e:
            print("AZURE ERROR: {}".format(e))
       

    def shutdown(self, modules):
        """
        Shutdown (can delete the container if needed)
        """
        #self.delete_via_container(self.container_name)
        pass
