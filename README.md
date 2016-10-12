#Modules Signing Script

Copyright Kieran Gillibrand 2016 (MIT License)

Small Python script which self signs kernel modules for any kernels newer than the currently booted one.

You will only need this if you wish to use unsigned kernel modules (Nvidia and VirtualBox in my case) and keep secure boot enabled. Most people I've seen online just disable secure boot but I don't think that's a brilliant soloution.

This script signs the kernel modules with your personal key. Be sure to keep your key files safe because anyone with these files can sign any module or execute any arbitrary code on your system once you have your key enrolled.

This is a personal project that's now released.

#Usage
- modulesFile: Mandatory first positional argument. JSON file that describes the modules to sign and the directory they are contained in. See below for the layout.
- privateKeyFile: Mandatory second positional argument. Your private key file for signing the modules (symlinks do not work for this arg).
- publicKeyFile: Mandatory third positional argument. Your public key file for signing the modules (symlinks do not work for this arg).
- -k/--kernels: Manually sign the provided kernels. Make sure to provide the correct format (see uname -r).
- -h: Show help.
- -d/--debug: Display extra information for debugging

#Preparation
- See this guide for instructions to create key files and enroll your private key: http://www.pellegrino.link/2015/11/29/signing-nvidia-proprietary-driver-on-fedora.html
(refer to the sections on creating keyfiles with openssl and then enrolling them with mokutil)
- See my gist with some updates to the guide if you want to try signing any modules manually: https://gist.github.com/Favorablestream/4b6822e14a6e1267b1c46049274c8e49
- Create your modules JSON file using the format below and provide it and your key files as command line parameters to the script.

JSON Modules File Layout:
```
{
    "moduleEntries": 
    [
        {
            "name": "Nvidia",
            "directory": "extra/nvidia/",
            "moduleFiles": ["nvidia-drm.ko", "nvidia.ko", "nvidia-modeset.ko", "nvidia-uvm.ko"]
        },
        
        {
            "name": "VirtualBox",
            "directory": "extra/VirtualBox/",
            "moduleFiles": ["vboxdrv.ko", "vboxguest.ko", "vboxnetadp.ko", "vboxnetflt.ko", "vboxpci.ko", "vboxsf.ko", "vboxvideo.ko"]
        }
    ]
}
```

Parameters
- name: Section name for the collection of modules
- directory: The directory where the modules are contained. 
This gets appended to: /usr/lib/modules/**KERNEL_VERSION_BEING_SIGNED**/
For example my modules for Nvidia are located in: /usr/lib/modules/4.7.2-201.fc24.x86_64/extra/nvidia
- moduleFiles: List of the module files to sign

Notes
- Make sure your format for this file is correct. Try: http://jsonlint.com and check this readme
- You can have more or less entries than me but make sure you have at least one section and at least one module file.
- Make sure you use the same key names that I do.

#Dependancies
- A Python 3 interpreter
- A Linux distro with the rpm, dpkg, or pacman package manager.
- The kernel-devel package (or equivalent for your distro, linux-headers-generic, etc) which provides the sign-file binary

#Script Operation

Automatic Mode
- Find the system package manager
- Find the currently booted kernel
- Find all installed kernels using the package manager
- Compare the kernel versions and find out which are newer than the currently booted one
- Parse the modules file and extract the modules to sign
- Build akmods for the kernels to sign if they don't exist
- Sign the modules for all new kernels

Manual Mode (-k/--kernels)
- Build akmods for the provided kernels if they don't exist
- Sign the modules for the provided kernel versions

#Notes and Issues
- This script requires root to sign the kernel modules. It will call sudo and prompt for your password before signing them. If you register it as a cron job be sure to do so as root.
- There is no standard way to find the system package manager so I call 3 popular ones (rpm, dpkg, and pacman in that order) and check the exit status. This means the first one will be detected if multiple are installed and that other package managers will not be detected.
- String parsing is based on regex and better than it was but could still break.
- This script depends on the module directories having the same name as the extracted kernel version strings.
- I haven't had the time to boot any virtual machines and test other configurations (mine is Fedora, rpm). I also haven't installed any new kernel versions lately to test if the signing process works on a new one. Signing an existing kernel (already signed) works fine for me though.
- I don't want to use external files to track state so the script will sign modules for any kernel newer than the current one even if they have already been signed. This has no ill effects on the modules though. Basically the script assumes that you will boot the new kernel at some point. You won't be able to boot (I get kicked into recovery mode after a timeout) if your current kernel has unsigned Nvidia modules (as long as you still have secure boot enabled) so the script assumes your current kernel modules are signed.
- There is no way for me to register this script to run when the akmod modules are first built or when a kernel is installed without building packages for various package managers.
- I found out the hard way that you can't use symlinks for your public or private key files so I added a note to the help for those argumants. The sign-file binary doesn't seem to accept a valid link to the files so I can't fix this.

#Downloading and Usage

1. Download modules-signing-script.pyc from the releases page or download a source code archive (includes the non-compiled script along with the License and Readme files).

2. Make the script executable

3. Make sure you have followed all the preparation steps above.

4. Run the script providing the modules file, private key file, and public key file as parameters, your modules will now be signed for all new kernels. Alternatively use the manual mode if the kernels you want signed are your current kernel or older.

5. Set it up as a root cron job if you want

#Constants
You might need to change these if you run into problems

executeCommandWithOutput ():
- ENCODING: The encoding used to decode the command output. Default: utf-8

signKernel ():
- SIGN_BINARY_PATH: Path to the sign-file binary for the current kernel. Default: /usr/src/kernels/**KERNEL_VERSION_BEING_SIGNED**/scripts/sign-file
- BASE_MODULES_PATH: The path that gets prepended to the modules path provided by each entry in the JSON file. Default: /usr/lib/modules/**KERNEL_VERSION_BEING_SIGNED**/
  Ex: /usr/lib/modules/4.7.2-201.fc24.x86_64/ + extra/Nvidia = /usr/lib/modules/4.7.2-201.fc24.x86_64/extra/Nvidia

#License
MIT License

Copyright (c) 2016 Kieran Gillibrand

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
