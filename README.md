#Nvidia Signing Script

Copyright Kieran Gillibrand 2016 (MIT License)

Small Python script which self signs Nivida's kernel modules for any kernels newer than the currently booted one.

You will only need this if you wish to use Nvidia's propietary drivers and keep secure boot enabled. Most people I've seen online just disable secure boot but I don't think that's a brilliant soloution.

Personal project now released.

#Usage
- -h: Show help.
- privateKeyFile: Mandatory first positional argument. Your private key file for signing the modules.
- publicKeyFile: Mandatory second positional argument. Your public key file for signing the modules.
- -debug/--debug: Display extra information for debugging

#Preparation
- See: http://www.pellegrino.link/2015/11/29/signing-nvidia-proprietary-driver-on-fedora.html and my gist with some updates: https://gist.github.com/Favorablestream/4b6822e14a6e1267b1c46049274c8e49 for instructions to create key files or to try signing the modules yourself.

#Dependancies
- A Python 3 interpreter
- A Linux distro with the rpm, dpkg, or pacman package manager.
- Nvidia akmod drivers installed with their dependancies.
- I believe kernel-devel is required for the sign-file binary that is called but kernel-devel is a dependancy for akmod drivers as far as I recall.

#Script Operation
- Find the system package manager
- Find the currently booted kernel
- Find all installed kernels using the package manager
- Compare the kernel versions and find out which are newer than the currently booted one
- Sign the modules for all new kernels

#Notes and Issues
- This script requires root to sign the kernel modules. It will call sudo and prompt for your password before signing them. If you register it as a cron job be sure to do so as root.
- There is no standard way to find the system package manager so I call 3 popular ones (rpm, dpkg, and pacman in that order) and check the exit status. This means the first one will be detected if multiple are installed and that other package managers will not be detected.
- String parsing is based on regex and better than it was but could still break.
- This script depends on the module directories having the same name as the extracted kernel version strings.
- I haven't had the time to boot any virtual machines and test other configurations (mine is Fedora, rpm). I also haven't installed any new kernel versions lately to test if the signing process works on a new one. Signing an existing kernel (already signed) works fine for me though.
- I don't want to use external files to track state so the script will sign any kernel newer than the current one even if it has already been signed. This has no ill effects though and the script shouldn't be much of a resource hog. Basically the script assumes that you will boot the new kernel at some point. You won't be able to boot (I get kicked into recovery mode after a timeout) if your current kernel has unsigned modules (as long as you still have secure boot enabled) so the script assumes your current kernel is signed.
- There is no way for me to register this script to run when the akmod modules are first built or when a kernel is installed as far as I'm aware. Modifying package install scripts will just get replaced when the package updates and might mess with checksums. I will probably run this as a cron job maybe once a day or so.

#Downloading and Usage

1. Download nvidia-signing-script.pyc from the releases page or download a source code archive (includes the non-compiled script along with the License and Readme files).

2. Make the script executable

3. Make sure you have your private and public keys generated

4. Run the script providing the private and public key files as parameters, your modules will now be signed for all new kernels

5. Set it up as a root cron job if you want

#Constants
You might need to change these if you run into problems

executeCommandWithOutput ():
- ENCODING: The encoding used to decode the command output. Default: utf-8

signKernel () (KERNEL_VERSION here refers to the kernel being signed not the booted one. It is a method parameter in signKernel () called kernel)
- SIGN_BINARY_PATH: Path to the sign-file binary for the current kernel. Default: /usr/src/kernels/**KERNEL_VERSION**/scripts/sign-file
- MODULES_PATH: Path to the Nivida kernel modules. Default: /usr/lib/modules/**KERNEL_VERSION**/extra/nvidia/
- MODULES_NAMES: A list of the Nivia modules to sign. Default: [nvidia-drm.ko, nvidia.ko, nvidia-modeset.ko, nvidia-uvm.ko]

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
