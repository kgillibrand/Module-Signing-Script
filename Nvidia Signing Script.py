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
__version__ = '0.1'
__date__ = '31/08/2016'
__maintainer__ = 'Kieran Gillibrand'
__email__ = 'Kieran.Gillibrand6@gmail.com'
__status__ = 'Personal Project (in development)'

#Imports
import sys

#Code
def handleError (errorMessage: str, exitCode: int)
'''
    Error handling function which displays a message and exits with an exit code.
    
    message (str): The message to display before exiting
    exitCode (int): The code to exit with
'''
    
    print (__title__ + ' Error: ' + errorMessage)
    print ()
    
    sys.exit (exitCode)

def getPackageManager () -> str:
    '''
        Returns the package manager for the current system or exits if it cannot be found.
        There is no standard way to find the package manager so this function simply tests if the following are installed: dpkg, dnf, yum, pacman
    '''
    
    #Each branch tries to run the package manager by checking it's version.
    #The package manager itself (ex: rpm) is called instead of a front end (ex: dnf) so more systems are covered
    #An argument like that should be one of the fastest for a package manager and returns an exit status of 0.
    #Just running the package manager with no arguments usually returns 1 in my experience even if it is installed.
    #If the package manager is not installed a status of 127 is usually returned.
    
    #dpkg (Debian based systems)
    if os.system ('dpkg --version') == 0:
        return 'dpkg'
        
    #rpm (Red hat based systems)
    else if os.system ('rpm --version') == 0:
        return 'dnf'
        
    #pacman (Arch linux based systems)
    else if os.system ('pacman --version') == 0:
        return 'pacman'
        
    #None of the above, sorry obscure package managers
    else:
        handleError ('Package manager could not be determined', 1)
    
def getInstalledKernels (packageManager: str) -> list:
    '''
        Returns a list of the currently installed kernels
    '''
    
def getNewKernels (currentKernel: str, installedKernels: list) -> list:
    '''
        Returns a list of all kernels that are newer than the currently booted one or exits if no kernels are newer than the currently booted one.
        
        currentKernel (str): The currently booted kernel
        installedKernels (list): A list of all the currently installed kernels
    '''
    
    SIGN_PATH = '/usr/src/kernels/' + currentKernel + '/scripts/sign-file'
    '''Path to the sign-file binary '''
    
def signKernel (kernel: str):
    '''
        Signs the nvidia kernel modules for a kernel
        
        kernel (str): The kernel whose modules to sign
    '''

def signNewKernels (newKernels: list):
    '''
        Signs the nvidia kernel modules for every new kernel by calling signKernel () on each
        
        newKernels (list): A list of the new kernels to sign
    '''

def main ():
    '''
        Main method for this script
    '''
    
if __name__ == '__main__'
    main ()
