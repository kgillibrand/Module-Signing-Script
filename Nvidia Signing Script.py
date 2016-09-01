#!/usr/bin/env python3

#License
'''
    MIT License

    Copyright (c) 2016 Kieran Gillibrand

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the 'Software'), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
'''
    
#Description
'''
    Nvidia Signing Script
    
    A small script which signs Nvidia's kernel modules for any installed kernel newer than the currently booted one.
    
    Will probably be run as a cron job. As of now I don't know how to run this when a new kernel is installed. Especially in a way independent of the package manager and package format.
'''

#Metadata
__title__ = 'Nvidia Signing Script'
__author__ = 'Kieran Gillibrand'
__host__ = 'https://github.com/Favorablestream'
__copyright__ = 'Copyright 2016 Kieran Gillibrand'
__credits__ = []
__license__ = 'MIT License (LICENSE.txt)'
__version__ = '0.2'
__date__ = '1/08/2016'
__maintainer__ = 'Kieran Gillibrand'
__email__ = 'Kieran.Gillibrand6@gmail.com'
__status__ = 'Personal Project (in development)'

#Imports
import sys

import subprocess

import os

#Code
def handleError (errorMessage: str, exitCode: int):
    '''
        Error handling function which displays a message and exits with an exit code (void).
    
        message (str): The message to display before exiting
        exitCode (int): The code to exit with
    '''
    
    print (__title__ + ' Error: ' + errorMessage)
    print ()
    
    sys.exit (exitCode)

def getPackageManager () -> str:
    '''
        Returns the package manager for the current system or exits if it cannot be found (str).
        There is no standard way to find the package manager so this function simply tests if the following are installed: dpkg, dnf, yum, pacman
    '''
    
    #Each branch tries to run the package manager by checking it's version.
    #The package manager itself (ex: rpm) is called instead of a front end (ex: dnf) so more systems are covered
    #Each is called with the --version argument since it should be one of the fastest for a package manager and returns an exit status of 0.
    #Just running the package manager with no arguments usually returns 1 in my experience even if it is installed.
    #If the package manager is not installed a status of 127 is usually returned, either way we just look for 0.
    #As is this will cause issues if multiple package managers are installed because only the first that is checked will be detected.
    
    #dpkg (Debian based systems)
    if os.system ('dpkg --version > /dev/null 2>&1') == 0:
        return 'dpkg'
        
    #rpm (Red hat based systems)
    elif os.system ('rpm --version > /dev/null 2>&1') == 0:
        return 'rpm'
        
    #pacman (Arch linux based systems)
    elif os.system ('pacman --version > /dev/null 2>&1') == 0:
        return 'pacman'
        
    #None of the above, sorry obscure package managers
    else:
        handleError ('Package manager could not be determined', 1)
    
def getCurrentKernel () -> str:
    '''
        Returns the current kernel version (str)
    '''
    
    return subprocess.check_output (['uname', '-r'])
    
def getInstalledKernels (packageManager: str) -> list:
    '''
        Returns a list of the currently installed kernels (list <str>).
        Calls a command depending on the package manager to list all installed kernels.
        
        packageManager (str): The system package manager fetched by getPackageManager ()
    '''
    
    outputString = None
    
    if packageManager == 'dpkg':
        output = subprocess.check_output (['dpkg', '--list', '|', 'grep', 'linux-image'])
        outputString = output.decode ('utf-8').rstrip ('\n')
        
    elif packageManager == 'rpm':
        output = subprocess.check_output (['rpm', '-qa', 'kernel'])
        outputString = output.decode ('utf-8').rstrip ('\n')
        
    elif packageManager == 'pacman':
        output = subprocess.check_output (['pacman', '-Q', '|', 'grep', 'linux'])
        outputString = output.decode ('utf-8').rstrip ('\n')
    
    installedKernels = outputString.split ('\n')
    
    return installedKernels
    
def compareKernels (kernel1: str, kernel2: str) -> int:
    '''
        Compares two kernel version strings (ex: 4.7.2-200 vs 4.5.5).
        Returns 1 if the first is newer (greater), -1 if the second is newer, and 0 if they are equal (int).
        Compares the first version strings (ex: 4.7.2) and the second (ex: -200) if the first two are equal.
        
        kernel1 (str): The first kernel
        kernel2 (str): The second kernel
    '''
    
    print ("kernel 1: %s" %kernel1)
    print ('kernel 2: %s' %kernel2)
    
    firstVersion1 = kernel1 [0:4]
    secondVersion1 = kernel1 [6:8]
    
    firstVersion2 = kernel2 [0:4]
    secondVersion2 = kernel2 [6:8]
    
    print ('firstVersion1: %s' %firstVersion1)
    print ('secondVersion1: %s' %secondVersion1)
    
    print ('firstVersion2: %s' %firstVersion2)
    print ('secondVersion2: %s' %secondVersion2)
    
    firstVersionNumber1 = int (firstVersion1)
    secondVersionNumber1 = int (secondVersion1)
    
    firstVersionNumber2 = int (firstVersion2)
    secondVersionNumber2 = int (secondVersion2)
    
    if firstVersionNumber1 > firstVersionNumber2:
        return 1
    
    elif firstVersionNumber1 < firstVersionNumber2:
        return -1
        
    else:
        if secondVersionNumber1 > secondVersionNumber2:
            return 1
            
        elif secondVersionNumber1 < secondVersionNumber2:
            return -1
            
        else:
            return 0
             
def getNewKernels (currentKernel: str, installedKernels: list) -> list:
    '''
        Returns a list of all kernels that are newer than the currently booted one or exits if no kernels are newer than the currently booted one (list <str>)
        
        currentKernel (str): The currently booted kernel
        installedKernels (list <str>): A list of all the currently installed kernels
    '''
        
    for installedKernel in installedKernels:
        returnValue = compareKernels (installedKernel, currentKernel)
        
        if returnValue == -1 or returnValue == 0:
            installedKernels.remove (installedKernel)
    
    return installedKernels
    
def signKernel (kernel: str, privateKeyPath: str, publicKeyPath: str):
    '''
        Signs the nvidia kernel modules for a kernel (void).
        
        kernel (str): The kernel whose modules to sign
        privateKeyPath (str): The path to the private key file to sign with
        publicKeyPath (str): The path to the public key file to sign with
    '''
    
    SIGN_BINARY_PATH = '/usr/src/kernels/' + kernel + '/scripts/sign-file'
    MODULES_PATH = '/usr/lib/modules/' + kernel + '/extra/nvidia/'
    MODULES = ['nvidia-drm.ko', 'nvidia.ko', 'nvidia-modeset.ko', 'nvidia-uvm.ko']
    
    subprocess.check_output ([SIGN_BINARY_PATH, 'sha256', privateKeyPath, publicKeyPath, MODULES_PATH + MODULES [0]])
    subprocess.check_output ([SIGN_BINARY_PATH, 'sha256', privateKeyPath, publicKeyPath, MODULES_PATH + MODULES [1]])
    subprocess.check_output ([SIGN_BINARY_PATH, 'sha256', privateKeyPath, publicKeyPath, MODULES_PATH + MODULES [2]])
    subprocess.check_output ([SIGN_BINARY_PATH, 'sha256', privateKeyPath, publicKeyPath, MODULES_PATH + MODULES [3]])

def signNewKernels (newKernels: list, privateKeyPath: str, publicKeyPath: str):
    '''
        Signs the nvidia kernel modules for every new kernel by calling signKernel () on each (void).
        
        newKernels (list <str>): A list of the new kernels to sign
        privateKeyPath (str): The path to the private key file to sign with
        publicKeyPath (str): The path to the public key file to sign with
    '''
    
    for newKernel in newKernels:
        signKernel (newKernel, privateKeyPath, publicKeyPath)
    
def main ():
    '''
        Main method for this script (void).
    '''
    
    packageManager = getPackageManager ()
    
    print ('Package manager: %s' %packageManager)
    
    installedKernels = getInstalledKernels (packageManager)
    
    print ('Installed kernels: %s' %installedKernels)
    
    currentKernel = getCurrentKernel ()
    
    print ('Current kernel: %s' %currentKernel)
    
    newKernels = getNewKernels (currentKernel, installedKernels)
    
    print ('New kernels: %s' %newKernels)
    
    signNewKernels (newKernels, privateKeyPath, publicKeyPath)
    
if __name__ == '__main__':
    main ()
