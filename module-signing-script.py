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
    
    A small script which signs kernel modules provided by a JSON file for any installed kernel newer than the currently booted one.
    
    Will probably be run as a cron job. As of now I don't know how to trigger this when a new kernel is installed. Especially in a way independent of the package manager and package format.
    
    Inspired by this guide: http://www.pellegrino.link/2015/11/29/signing-nvidia-proprietary-driver-on-fedora.html and by my gist which corrects some out of date things: https://gist.github.com/Favorablestream/4b6822e14a6e1267b1c46049274c8e49
'''

#Metadata
__title__ = 'Module Signing Script'
__author__ = 'Kieran Gillibrand'
__host__ = 'https://github.com/Favorablestream/Module-Signing-Script'
__copyright__ = 'Copyright 2016 Kieran Gillibrand'
__credits__ = []
__license__ = 'MIT License (LICENSE.txt)'
__version__ = '1.2'
__date__ = '13/09/2016'
__maintainer__ = 'Kieran Gillibrand'
__email__ = 'Kieran.Gillibrand6@gmail.com'
__status__ = 'Personal Project (in development)'

#Imports
import sys #exit ()

import subprocess #check_output (), call ()

import argparse #ArgumentParser ()

import re #search () (Regular expressions)

import pkg_resources #parse_version (Kernel Version comparisions)

import os #getuid ()

import json #loads () (JSON parsing)

import contextlib #contextmanager (Changing working directory)

import os.path #isfile ()

DEBUG = False
'''Global flag for debuging print statements, set by -debug/--debug'''

#Helper methods called by other methods
def handleError (errorMessage: str, exitCode: int, exception: Exception = None):
    '''
        Error handling function which displays a message, prints an exception (if provided), and exits with an exit code (void).
    
        message (str): The message to display before exiting
        exitCode (int): The code to exit with
        exception (Exception) (optional): The exception to print
        
        Script Exit codes
        - 0: Success, normal exit code
        - 1: Package manager not found
        - 2: Unable to sign a kernel module
        - 3: Unable to extract the kernel version string
        - 4: Cannot open modules JSON file
        - 5: Modules JSON content is malformed
        - 6: Cannot access modules directory
        - 7: Cannot build akmods for kernel
    '''
    
    exitCodes = ['Success, normal exit', 'Package manager not found', 'Unable to sign a kernel module', 'Unable to extract kernel version string', 'Cannot open modules JSON file', 'Modules JSON content is malformed', 'Cannot access modules directory', 'Cannot build akmods for kernel']
    
    print (__title__ + ': Error: ' + errorMessage)
    print ()
    
    if exception != None:
        print (str (exception))
        print ()
        
    print ('Exiting with exit code: %d, %s' %(exitCode, exitCodes [exitCode]))
    
    sys.exit (exitCode)

def executeCommandWithOutput (commandName: str, commandArgs: list = []) -> str:
    '''
        Fetches a process output and decodes it as a utf-8 string (by default) (str)
        
        commandName (str): The name of the command to run
        commandArgs (list <string>) (optional): The arguments to supply to the command (-r, etc)
    '''
    
    ENCODING = 'utf-8'
    '''Encoding to use for decoding process output'''
    
    commandArgs.insert (0, commandName) #check_output () expects the command and it's arguments in the same list
    
    try:
        responseBytes = subprocess.check_output (commandArgs)
        
    #An exception is raised if the command does not exist, pass it to the caller
    except (OSError) as executeError:
        raise executeError
        
    return responseBytes.decode (ENCODING)
    
def executeCommandWithExitStatus (commandName: str, commandArgs: list = []) -> int:
    '''
        Run a command without fetching the output while piping all output streams to /dev/null then return the program exit status (int)
        
        commandName (str): The name of the command to run
        commandArgs (list <string>) (optional): The arguments to supply to the command (-r, etc)
    '''    
    
    commandArgs.insert (0, commandName) #call () expects the command and it's arguments in the same list
                
    try:
        exitStatus = subprocess.call (args = commandArgs, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
        
    #An exception is raised if the command does not exist, return 127 status instead
    except (OSError) as executeError:
        exitStatus = 127
        
    return exitStatus

def extractKernelVersionString (inputLine: str) -> str:
    '''
        Extracts a kernel version string (Ex: 4.7.2-201.fc24.x86_64) from a line of text (str)
        Be sure to strip trailing newlines with rstrip () if you are splitting multiline output on newlines so that you don't pass an empty line to this method.
    
        inputLine (str): The line of output to extract the version string from
    '''
    
    match = re.search ('\d+(\d+|\.|\-|\_|[a-z]|[A-Z])*', inputLine) #Match a digit then more digits, decimal points, dashes, or letters
        
    if match == None:
        handleError ('Unable to extract version string for input line: %s' %inputLine, 3)
            
    versionString = match.group (0)
        
    #Sometimes . or - are used as a seperator and are picked up as the last character so remove that last character if it isn't a digit or letter
    if not (versionString [-1:].isdigit () or versionString [-1:].isalpha ()):
        versionString = versionString [:-1]
            
    return versionString
    
def compareKernels (kernel1: str, kernel2: str) -> int:
    '''
        Compares two kernel version strings (ex: 4.7.2-200.fc24.x86_64 vs 4.5.5.fc24.x86_64).
        Returns 1 if kernel1 is newer (greater), -1 if kernel2 is newer, and 0 if they are equal (int).
        
        kernel1 (str): The first kernel version string
        kernel2 (str): The second kernel version string
    '''

    if DEBUG:
        print ('---------------------------------------------')
        print ('Kernel version comparison')
        print ('Kernel version 1: %s' %kernel1)
        print ('Kernel version 2: %s' %kernel2)
        print ()
    
    kernel1Version = pkg_resources.parse_version (kernel1)
    kernel2Version = pkg_resources.parse_version (kernel2)
    
    comparisonValue = 0
    
    if kernel1Version > kernel2Version:
        comparisonValue = 1
        
        if DEBUG:
            print ('Kernel version 1 evaluated as newer')
        
    elif kernel1Version < kernel2Version:
        comparisonValue = -1
        
        if DEBUG:
            print ('Kernel version 2 evaluated as newer')
        
    else:        
        if DEBUG:
            print ('Kernel versions evaluated as equal')
        
    if DEBUG:
        print ('Return value: %d' %comparisonValue)
        print ('---------------------------------------------')
        print ()
    
    return comparisonValue
    
def getModuleEntries (modulesPath: str) -> list:
    '''
        Parses the provided JSON file to get information for the modules to sign as a list of module entries (list)
        
        modulesPath (str): The path to the modules JSON file
    '''
    
    try:
        with open (modulesPath) as modulesFile:
            if DEBUG:
                print ('Using modules file: \'%s\'' %modulesPath)
                print ()
                    
            modules = json.loads (modulesFile.read ())

    except (IOError, OSError) as fileError:
        handleError (message = 'Modules file: \'%s\' does not exist or cannot be opened' %modulesPath, exception = fileError, exitCode = 4)
        
    except (ValueError) as jsonError:
        handleError (message = 'Modules JSON file: \'%s\' is malformed, refer to the README or the exception message below for the correct format' %modulesPath, exception = jsonError, exitCode = 5)
        
    return modules ["moduleEntries"]

def buildAkmods (kernel: str):
    '''
        Build the kernel modules for a kernel (void)
        The akmods command exits with 0 if it builds modules or if they already exist for the specified kernel
        --force causes akmods to run even building the modules previously failed
        akmods requires root so sudo is called
        
        kernel (str): The kernel to build modules for
    '''
    if executeCommandWithExitStatus ('sudo', ['akmods', '--kernels', kernel, '--force']) != 0:
        handleError (errorMessage = 'Could not build akmods for kernel: %s' %kernel, exitCode = 7)
    
@contextlib.contextmanager
def changeWorkingDirectory (newDirectory: str):
    '''
        Generator method to change directory in an exception safe way (always returns to the original directory) (generator)
        Borrowed from Stack Overflow after some research on how it works
        
        newDirectory (str): The directory to switch to
    '''
    previousDirectory = os.getcwd ()
    
    os.chdir (os.path.expanduser (newDirectory))
    
    try:
        yield #Return until we're done with the generator
        
    finally:
        os.chdir (previousDirectory) #Run once we're done
        
def signKernel (kernel: str, moduleEntries: list, privateKeyPath: str, publicKeyPath: str):
    '''
        Signs the nvidia kernel modules for a kernel (void).
        
        kernel (str): The kernel whose modules to sign
        privateKeyPath (str): The path to the private key file to sign with
        publicKeyPath (str): The path to the public key file to sign with
    '''
    
    SIGN_BINARY_PATH = '/usr/src/kernels/' + kernel + '/scripts/sign-file'
    '''Path to the sign-file binary used to sign the kernel modules'''
    
    BASE_MODULES_PATH = '/usr/lib/modules/' + kernel + '/'
    '''Path to modules before the directory provided by each module entry is appended'''
    
    #Print if the user is not root (uid 0)
    if os.getuid () != 0:
        print ('%s: Building kernel modules and signing them must be done as root. You may be prompted for your password:' %__title__)
        print ()
        
    buildAkmods (kernel)
    
    if DEBUG:
        print ('Akmods have been built for kernel: %s or they already exist' %kernel)
        print ()
        
    #Sign the modules for each entry in the JSON file
    for moduleEntry in moduleEntries:
        modulesPath = BASE_MODULES_PATH + moduleEntry ['directory']
        
        try:
            with changeWorkingDirectory (modulesPath):
                moduleFiles = moduleEntry ['moduleFiles']
                                
                if DEBUG:
                    print ('Switched to modules directory: %s' %modulesPath)
                    print ('Kernel module files: %s' %moduleEntry ['moduleFiles'])
                    print ()
            
                #Sign all the modules in the list of modules and call handleError if the exit status is not 0
                #The sign-file binary needs to be called as root so sudo is called each time (though sudo was already called by buildAkmods ())
                #If this script is set up as a root cron job or the entire script is run as root then the sudo call isn't nessecary but has no effect
                for moduleFile in moduleFiles:
                    if DEBUG:
                        print ('Signing kernel module: %s' %moduleFile)

                    if executeCommandWithExitStatus ('sudo', [SIGN_BINARY_PATH, 'sha256', privateKeyPath, publicKeyPath, moduleFile]) != 0:
                        handleError ('Error signing kernel module: %s (Check your password for sudo, that both your keyfiles have correct paths/exist, and the module entries in your json file)' %moduleFile, 2)
                
                if DEBUG:
                    print ()
        
        except (FileNotFoundError) as directoryError:
            handleError (errorMessage = 'Could not move to modules directory: %s' %modulesPath, exception = directoryError, exitCode = 6)
            
#Core methods called by main ()
def getPackageManager () -> str:
    '''
        Returns the package manager for the current system (str)
        There is no standard way to find the package manager so this function simply tests if the following are installed: rpm, dpkg, pacman
    '''
    
    #Each branch tries to run the package manager by checking it's version.
    #The package manager itself (ex: rpm) is called instead of a front end (ex: dnf) so more systems are covered
    #Each is called with the --version argument since it should be one of the fastest commands for a package manager and returns an exit status of 0.
    #Just running the package manager with no arguments usually returns an exit code of 1 in my experience even if it is installed.
    #If the package manager is not installed a status of 127 is usually returned, either way we just look for 0.
    #As is this will cause issues if multiple package managers are installed because only the first that is checked will be detected.
        
    #rpm (Red hat based systems)
    if executeCommandWithExitStatus ('rpm', ['--version']) == 0:
        return 'rpm'
        
    #dpkg (Debian based systems)
    elif executeCommandWithExitStatus ('dpkg', ['--version']) == 0:
        return 'dpkg'
        
    #pacman (Arch linux based systems)
    elif executeCommandWithExitStatus ('pacman', ['--version']) == 0:
        return 'pacman'
        
    #None of the above, sorry obscure package managers
    else:
        handleError ('Package manager could not be determined', 1)
    
def getCurrentKernel () -> str:
    '''
        Returns the current kernel version (str)
    '''
    
    unameOutput = executeCommandWithOutput ('uname', ['-r'])

    unameOutput.rstrip () #Single line output still contains trailing newline
    
    return extractKernelVersionString (unameOutput)
            
def getInstalledKernels (packageManager: str) -> list:
    '''
        Returns a list of the currently installed kernels (list <str>).
        Calls a command depending on the package manager to list all installed kernels.
        
        packageManager (str): The system package manager fetched by getPackageManager ()
    '''
        
    if packageManager == 'rpm':
        output = executeCommandWithOutput ('rpm', ['-qa', 'kernel'])
        
    elif packageManager == 'dpkg':
        output = executeCommandWithOutput ('dpkg', ['--list', '|', 'grep', 'linux-image'])
        
    elif packageManager == 'pacman':
        output = executeCommandWithOutput ('pacman', ['-Q', '|', 'grep', 'linux'])

    output = output.rstrip ()
    
    outputLines = output.split ('\n')
    
    kernelVersions = []
    
    for line in outputLines:
        versionString = extractKernelVersionString (line)
            
        kernelVersions.append (versionString)
        
    return kernelVersions
        
def getNewKernels (currentKernel: str, installedKernels: list) -> list:
    '''
        Returns a list of all kernels that are newer than the currently booted one or exits if no kernels are newer than the currently booted one (list <str>)
        
        currentKernel (str): The currently booted kernel
        installedKernels (list <str>): A list of all the currently installed kernels
    '''
        
    newKernels = []
    
    #Compare kernels and add them to the newKernels list if they are newer than the currently booted one
    for installedKernel in installedKernels:        
        if compareKernels (installedKernel, currentKernel) == 1:
            newKernels.append (installedKernel)
    
    return newKernels
    
def signNewKernels (newKernels: list, moduleEntries: list, privateKeyPath: str, publicKeyPath: str):
    '''
        Signs the nvidia kernel modules for every new kernel by calling signKernel () on each (void).
        
        newKernels (list <str>): A list of the new kernels to sign
        privateKeyPath (str): The path to the private key file to sign with
        publicKeyPath (str): The path to the public key file to sign with
    '''
    
    for newKernel in newKernels:
        signKernel (newKernel, moduleEntries, privateKeyPath, publicKeyPath)
    
def main ():
    '''
        Main method for this script (void).
    '''
        
    print ()
    print ('%s - %s, %s' %(__title__, __copyright__, __license__))
    print ('Version: %s, %s' %(__version__, __date__))
    print ('%s' %__host__)
    print ()
    
    parser = argparse.ArgumentParser (description = 'Nvidia Signing Script: A small script which signs Nvidia\'s kernel modules for any installed kernel newer than the currently booted one.')
    parser.add_argument ('modulesFile', help = '(Mandatory) Your modules JSON file specifying the modules that you want to sign (see README for details)')
    parser.add_argument ('privateKeyFile', help = '(Mandatory) Your private key file for signing the kernel modules (see README for details)')
    parser.add_argument ('publicKeyFile', help = '(Mandatory) Your public key file for signing the kernel modules (see README for details)')
    parser.add_argument ('-k', '--kernels', type = str, nargs = '+', help = '(Optional) Sign the modules only for the provided kernels. Make sure to format them correctly (see uname -r output)')
    parser.add_argument ('-d', '--debug', help = '(Optional) Display extra print statements for debugging', action = 'store_true')
    args = parser.parse_args ()
    
    global DEBUG 
    DEBUG = args.debug
    
    moduleEntries = getModuleEntries (args.modulesFile)
    
    print ('%s: Signing modules for: ' %__title__, end = '')
    for moduleEntry in moduleEntries:
        print (moduleEntry ['name'], end = ', ')
    print ('\n')
    
    #Manual mode (-k/--kernels is present)
    if args.kernels != None:
        print ('%s: Running in manual mode' %__title__)
        print ()
        print ('%s: Provided kernels: %s' %(__title__, args.kernels))
        print ()
        
        for kernel in args.kernels:
            kernelVersion = extractKernelVersionString (kernel) #Will exit if the argument is not a proper version string
            
            print ('%s: Signing provided kernel: %s' %(__title__, kernelVersion))
            print ()
            
            signKernel (kernelVersion, moduleEntries, args.privateKeyFile, args.publicKeyFile)
        
        print ('%s: Kernel modules for provided kernel(s) have been signed' %__title__)
        print ()
        
    #Else automatic mode
    else:
        print ('%s: Running in automatic (new kernels) mode' %__title__)
        print ()
        
        packageManager = getPackageManager ()
        
        print ('%s: Found package manager: %s' %(__title__, packageManager))
        print ()
        
        currentKernel = getCurrentKernel ()

        print ('%s: Found current kernel: %s' %(__title__, currentKernel))
        print ()
        
        installedKernels = getInstalledKernels (packageManager)
        
        print ('%s: Found installed kernels: %s' %(__title__, installedKernels))
        print ()
        
        newKernels = getNewKernels (currentKernel, installedKernels)
        
        if len (newKernels) > 0:
            print ('%s: Found new kernels: %s' %(__title__, newKernels))
            print ()
            
            signNewKernels (newKernels, moduleEntries, args.privateKeyFile, args.publicKeyFile)
        
            print ('%s: Kernel modules for new kernels have been signed' %__title__)
            print ()
        
        else:
            print ('%s: No new kernels found' %__title__)
            print ()
    
if __name__ == '__main__':
    main ()
