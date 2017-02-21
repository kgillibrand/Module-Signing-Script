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
__version__ = '1.3'
__date__ = '22/12/2016'
__maintainer__ = 'Kieran Gillibrand'
__email__ = 'Kieran.Gillibrand6@gmail.com'
__status__ = 'Personal Project (in development)'

#Imports
import sys
import os
import subprocess

import argparse

import re
import pkg_resources

import json

import contextlib

DEBUG = False
'''Global flag for debuging print statements, set by -debug/--debug'''

#Helper methods called by other methods
def debug_print (message: str, print_newline: bool = True):
    '''
        Print a message if debugging statements are enabled
        
        message (str): The message to print
        print_newline (bool): Print an additional newline after the message (default True) 
    '''
    
    if not DEBUG:
        return
        
    print (message)
    
    if print_newline:
        print ()
        
def non_debug_print (message: str, print_newline: bool = True):
    '''
        Print a message if debugging statements are not enabled
        
        message (str): The message to print
        print_newline (bool): Print an additional newline after the message (default True)
    '''
    
    if DEBUG:
        return
    
    print (message)
    
    if print_newline:
        print ()


def handle_error (message: str, exit_code: int, exception: Exception = None, command_exitcode: int = 0):
    '''
        Error handling function which displays a message, prints an exception (if provided), and exits with an exit code (void).
    
        message (str): The message to display before exiting
        exit_code (int): The code to exit with
        exception (Exception) (optional): The exception to print
        command_exitcode (int) (optional): The exit code of the command that caused the error
        
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
    
    exit_codes = ['Success, normal exit', 'Package manager not found', 'Unable to sign a kernel module', 'Unable to extract kernel version string', 'Cannot open modules JSON file', 'Modules JSON content is malformed', 'Cannot access modules directory', 'Cannot build akmods for kernel']
    
    print ('Error: ' + message)
    
    if command_exitcode != 0:
        print ('Last command exited with code %d' %command_exitcode)
        
    print ()
    
    if exception != None:
        print (str (exception))
        print ()
        
    print ('Exiting with exit code: %d, %s' %(exit_code, exit_codes [exit_code]))
    
    sys.exit (exit_code)

def execute_with_output (command: str, args: list = []) -> str:
    '''
        Fetches a process output, decodes it as a utf-8 string (by default), and returns it (str)
        
        command (str): The name of the command to run
        args (list <string>) (optional): The arguments to supply to the command (-r, etc)
    '''
    
    ENCODING = 'utf-8'
    '''Encoding to use for decoding process output'''
    
    args.insert (0, command) #check_output () expects the command and it's arguments in the same list
    
    try:
        response_bytes = subprocess.check_output (args)
        
    #An exception is raised if the command does not exist, pass it to the caller
    except (OSError):
        raise
        
    return response_bytes.decode (ENCODING)
    
def execute_with_exit_status (command: str, args: list = []) -> int:
    '''
        Run a command without fetching the output while piping all output streams to /dev/null then return the program exit status (int)
        
        commandName (str): The name of the command to run
        commandArgs (list <string>) (optional): The arguments to supply to the command (-r, etc)
    '''    
    
    args.insert (0, command) #call () expects the command and it's arguments in the same list
                
    try:
        exitStatus = subprocess.call (args, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
        
    #An exception is raised if the command does not exist, return 127 status instead
    except (OSError):
        exitStatus = 127
        
    return exitStatus

def extract_kernel_version (input_line: str) -> str:
    '''
        Extracts a kernel version string (Ex: 4.7.2-201.fc24.x86_64) from a line of text (str)
        Be sure to strip trailing newlines with rstrip () if you are splitting multiline output on newlines so that you don't pass an empty line to this method.
    
        input_line (str): The line of output to extract the version string from
    '''
    
    match = re.search ('\d+(\d+|\.|\-|\_|[a-z]|[A-Z])*', input_line) #Match a digit then more digits, decimal points, dashes, or letters
        
    if match == None:
        handle_error ('Unable to extract version string for input line: %s' %inputLine, exit_code = 3)
            
    version_string = match.group (0)
        
    #Sometimes . or - are used as a seperator and are picked up as the last character so remove that last character if it isn't a digit or letter
    if not (version_string [-1:].isdigit () or version_string [-1:].isalpha ()):
        version_string = version_string [:-1]
            
    return version_string
    
def compare_kernels (kernel1: str, kernel2: str) -> int:
    '''
        Compares two kernel version strings (ex: 4.7.2-200.fc24.x86_64 vs 4.5.5.fc24.x86_64).
        Returns 1 if kernel1 is newer (greater), -1 if kernel2 is newer, and 0 if they are equal (int).
        
        kernel1 (str): The first kernel version string
        kernel2 (str): The second kernel version string
    '''

    debug_print ('---------------------------------------------', print_newline = False)
    debug_print ('Kernel version comparison', print_newline = False)
    debug_print ('Kernel version 1: %s' %kernel1, print_newline = False)
    debug_print ('Kernel version 2: %s' %kernel2)
    
    kernel1_version = pkg_resources.parse_version (kernel1)
    kernel2_version = pkg_resources.parse_version (kernel2)
    
    comparison_value = 0
    
    if kernel1_version > kernel2_version:
        comparison_value = 1
        
        debug_print ('Kernel version 1 evaluated as newer')
        
    elif kernel1_version < kernel2_version:
        comparison_value = -1
        
        debug_print ('Kernel version 2 evaluated as newer')
        
    else:        
        debug_print ('Kernel versions evaluated as equal')
        
    debug_print ('Return value: %d' %comparison_value, print_newline = False)
    debug_print ('---------------------------------------------')
    
    return comparison_value
    
def get_module_entries (modules_path: str) -> list:
    '''
        Parses the provided JSON file to get information for the modules to sign as a list of module entries (list)
        
        modules_path (str): The path to the modules JSON file
    '''
    
    try:
        with open (modules_path) as modules_file:
            debug_print ('Using modules file: \'%s\'' %modules_path)
                    
            modules = json.loads (modules_file.read ())

    except (IOError, OSError) as file_error:
        handle_error ('Modules file: \'%s\' does not exist or cannot be opened' %modules_path, exception = file_error, exit_code = 4)
        
    except (ValueError) as json_error:
        handle_error ('Modules JSON file: \'%s\' is malformed, refer to the README or the exception message below for the correct format' %modules_path, exception = json_error, exit_code = 5)
        
    return modules ["module_entries"]

def build_akmods (kernel: str):
    '''
        Build the kernel modules for a kernel (void)
        The akmods command exits with 0 if it builds modules or if they already exist for the specified kernel
        --force causes akmods to run even building the modules previously failed
        akmods requires root so sudo is called
        
        kernel (str): The kernel to build modules for
    '''
    if execute_with_exit_status ('sudo', ['akmods', '--kernels', kernel, '--force']) != 0:
        handle_error ('Could not build akmods for kernel: %s' %kernel, exit_code = 7)
    
@contextlib.contextmanager
def change_working_directory (new_directory: str):
    '''
        Generator method to change directory in an exception safe way (always returns to the original directory) (generator)
        Borrowed from Stack Overflow after some research on how it works
        
        new_directory (str): The directory to switch to
    '''
    previous_directory = os.getcwd ()
    
    os.chdir (os.path.expanduser (new_directory))
    
    try:
        yield #Return until we're done with the generator
        
    finally:
        os.chdir (previous_directory) #Run once we're done
        
def sign_kernel (kernel: str, module_entries: list, private_key_path: str, public_key_path: str):
    '''
        Signs the kernel modules for a kernel (void).
        
        kernel (str): The kernel whose modules to sign
        private_key_path (str): The path to the private key file to sign with
        public_key_path (str): The path to the public key file to sign with
    '''
    
    SIGN_BINARY_PATH = '/usr/src/kernels/' + kernel + '/scripts/sign-file'
    '''Path to the sign-file binary used to sign the kernel modules'''
    
    BASE_MODULES_PATH = '/usr/lib/modules/' + kernel + '/'
    '''Path to modules before the directory provided by each module entry is appended'''
    
    #Print if the user is not root (uid 0)
    if os.getuid () != 0:
        print ('Building kernel modules and signing them must be done as root. You may be prompted for your password:')
        print ()
        
    build_akmods (kernel)
    
    debug_print ('Akmods have been built for kernel: %s or they already exist' %kernel)
        
    #Sign the modules for each entry in the JSON file
    for module_entry in module_entries:
        modules_path = BASE_MODULES_PATH + module_entry ['directory']
        
        try:
            with change_working_directory (modules_path):
                module_files = module_entry ['module_files']
                                
                debug_print ('Switched to modules directory: %s' %modules_path, print_newline = False)
                debug_print ('Kernel module files: %s' %module_entry ['module_files'])
            
                #Sign all the modules in the list of modules and call handle_error if the exit status is not 0
                #The sign-file binary needs to be called as root so sudo is called each time (though sudo was already called by build_akmods ())
                #If this script is set up as a root cron job or the entire script is run as root then the sudo call isn't nessecary but has no effect
                for module in module_files:
                    debug_print ('Signing kernel module: %s' %module, print_newline = False)

                    sign_status = execute_with_exit_status ('sudo', [SIGN_BINARY_PATH, 'sha256', private_key_path, public_key_path, module])
                    if sign_status != 0:
                        handle_error ('Error signing kernel module: %s (Check your password for sudo, that both your keyfiles have correct paths/exist, and the module entries in your json file)' %module, exit_code = 2, command_exitcode = sign_status)
        
        except (FileNotFoundError) as directory_error:
            handle_error ('Could not move to modules directory: %s' %modules_path, exception = directory_error, exit_code = 6)
            
#Core methods called by main ()
def get_package_manager () -> str:
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
    if execute_with_exit_status ('rpm', ['--version']) == 0:
        return 'rpm'
        
    #dpkg (Debian based systems)
    elif execute_with_exit_status ('dpkg', ['--version']) == 0:
        return 'dpkg'
        
    #pacman (Arch linux based systems)
    elif execute_with_exit_status ('pacman', ['--version']) == 0:
        return 'pacman'
        
    #None of the above, sorry obscure package managers
    else:
        handle_error ('Package manager could not be determined', 1)
    
def get_current_kernel () -> str:
    '''
        Returns the current kernel version (str)
    '''
    
    uname_output = execute_with_output ('uname', ['-r'])
    uname_output.rstrip () #Single line output still contains trailing newline
    
    return extract_kernel_version (uname_output)
            
def get_installed_kernels (package_manager: str) -> list:
    '''
        Returns a list of the currently installed kernels (list <str>).
        Calls a command depending on the package manager to list all installed kernels.
        
        packageManager (str): The system package manager fetched by get_package_manager ()
    '''
        
    if package_manager == 'rpm':
        output = execute_with_output ('rpm', ['-qa', 'kernel'])
        
    elif package_manager == 'dpkg':
        output = execute_with_output ('dpkg', ['--list', '|', 'grep', 'linux-image'])
        
    elif packageManager == 'pacman':
        output = execute_with_output ('pacman', ['-Q', '|', 'grep', 'linux'])

    output = output.rstrip ()
    output_lines = output.split ('\n')
    
    kernel_versions = []
    for line in output_lines:
        version_string = extract_kernel_version (line)
            
        kernel_versions.append (version_string)
        
    return kernel_versions
        
def get_new_kernels (current_kernel: str, installed_kernels: list) -> list:
    '''
        Returns a list of all kernels that are newer than the currently booted one or exits if no kernels are newer than the currently booted one (list <str>)
        
        current_kernel (str): The currently booted kernel
        installed_kernels (list <str>): A list of all the currently installed kernels
    '''
        
    new_kernels = []
    
    #Compare kernels and add them to the newKernels list if they are newer than the currently booted one
    for installed_kernel in installed_kernels:        
        if compare_kernels (installed_kernel, current_kernel) == 1:
            new_kernels.append (installed_kernel)
    
    return new_kernels
    
def sign_new_kernels (new_kernels: list, module_entries: list, private_key_path: str, public_key_path: str):
    '''
        Signs the nvidia kernel modules for every new kernel by calling sign_kernel () on each (void).
        
        newKernels (list <str>): A list of the new kernels to sign
        private_key_path (str): The path to the private key file to sign with
        public_key_path (str): The path to the public key file to sign with
    '''
    
    for new_kernel in new_kernels:
        sign_kernel (new_kernel, module_entries, private_key_path, public_key_path)
    
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
    parser.add_argument ('modules_file', help = '(Mandatory) Your modules JSON file specifying the modules that you want to sign (see README for details)')
    parser.add_argument ('private_key_file', help = '(Mandatory) Your private key file for signing the kernel modules (see README for details)')
    parser.add_argument ('public_key_file', help = '(Mandatory) Your public key file for signing the kernel modules (see README for details)')
    parser.add_argument ('-k', '--kernels', type = str, nargs = '+', help = '(Optional) Sign the modules only for the provided kernels. Make sure to format them correctly (see uname -r output)')
    parser.add_argument ('-d', '--debug', help = '(Optional) Display extra print statements for debugging', action = 'store_true')
    args = parser.parse_args ()
    
    global DEBUG 
    DEBUG = args.debug
    
    module_entries = get_module_entries (args.modules_file)
    
    print ('Signing modules for: ', end = '')
    for module_entry in module_entries:
        print (module_entry ['name'], end = ', ')
    print ()
    
    #Manual mode (-k/--kernels is present)
    if args.kernels != None:
        print ('Running in manual mode')
        print ()
        print ('Provided kernels: %s' %args.kernels)
        print ()
        
        for kernel in args.kernels:
            kernel_version = extract_kernel_version (kernel) #Will exit if the argument is not a proper version string
            
            print ('Signing provided kernel: %s' %kernel_version)
            print ()
            
            sign_kernel (kernel_version, module_entries, args.private_key_file, args.public_key_file)
        
        print ('Kernel modules for provided kernel(s) have been signed')
        print ()
        
    #Else automatic mode
    else:
        print ('Running in automatic (new kernels) mode')
        print ()
        
        packageManager = get_package_manager ()
        
        print ('Found package manager: %s' %packageManager)
        
        currentKernel = get_current_kernel ()

        print ('Found current kernel: %s' %currentKernel)
        
        installedKernels = get_installed_kernels (packageManager)
        
        print ('Found installed kernels: %s' %installedKernels)
        
        newKernels = get_new_kernels (currentKernel, installedKernels)
        
        if len (newKernels) > 0:
            print ('Found new kernels: %s' %newKernels)
            print ()
            
            sign_new_kernels (newKernels, module_entries, args.private_key_file, args.public_key_file)
        
            print ('Kernel modules for new kernels have been signed')
        
        else:
            print ('No new kernels found')
            
if __name__ == '__main__':
    main ()
