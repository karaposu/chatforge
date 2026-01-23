Skip to content
Navigation Menu
unoconv
unoconv

Type / to search
Code
Issues
35
Pull requests
Actions
Projects
Wiki
Security
Insights
This repository was archived by the owner on Mar 31, 2025. It is now read-only.
Not working on Mac #27
Closed
Closed
Not working on Mac
#27
@sotis
Description
sotis
opened on Feb 15, 2012
I get the following error on my macbook:

unoconv: Cannot find a suitable pyuno library and python binary combination in /Applications/OpenOffice.org.app/Contents
ERROR: Please locate this library and send your feedback to:
http://github.com/dagwieers/unoconv/issues
No module named uno
unoconv: Cannot find a suitable office installation on your system.
ERROR: Please locate your office installation and send your feedback to:
http://github.com/dagwieers/unoconv/issues

I'm running OpenOffice.org 3.3.0 on Mac OS X Lion 10.7.2
My unoconv version is 0.5, it is placed in /usr/bin and given read and execute permissions

It fails if called directly, also if called with sudo

Searched for openoffice files and found:
pyuno.so at /Applications/OpenOffice.org.app/Contents/basis-link/program/pyuno.so
soffice.bin at /Applications/OpenOffice.org.app/Contents/MacOS/soffice.bin

Activity
dagwieers
dagwieers commented on Feb 15, 2012
dagwieers
on Feb 15, 2012
Member
Arghl, yet another location to add to my search path, only for the office binary :-/ So someone decided to add 'MacOS' to the directory structure...

Can you tell me what the location is of the python.bin ? I am afraid I have to do another rewrite of the search-code just to accomodate for the possibility to have soffice.bin inside a MacOS folder. Let's hope the python binary is in that same folder...

ghost assigned 
dagwieers
on Feb 15, 2012
sotis
sotis commented on Feb 15, 2012
sotis
on Feb 15, 2012
Author
Thanks for the quick reply Dag,

Here's what I've discovered so far:

First of all it looks like an operating system version issue rather than an office version one. My iMac which also runs Mac OS X Lion but has libreoffice installed, has the exact same problem.

Now, to make matters worse, it looks like there's no python.bin file

I tried to do a "locate python.bin" and a "find / -name python.bin -print" both with or without sudo and ended up empty hahnded. python.bin is nowhere to be found.
Is it possible that htey've changed the name of the file? Where is it generally supposed to be?
A python interpreter IS installed on my machine (python -V returns "Python 2.7.1") but that's the system one and I guess it's not the one you're after. It's in /usr/bin anyway as it should

dagwieers
dagwieers commented on Feb 15, 2012
dagwieers
on Feb 15, 2012
Member
Ok, the reason why unoconv is looking for a python interpreter inside the LibreOffice installation path, is because that's the only guaranteed way to make sure python and the python UNO bindings are working together. In many cases, if the python UNO module has been compiled for a different python version, it fails to work.

Now, it is not required to have a python.bin, it might actually work with the python you have installed, especially if the LibreOffice and python interpreter come from the same "repository". Anyway, assuming this is the case for everyone I will add the MacOS case to the unoconv tool so you can test.

Can you test the newer version in Github ? Thanks !

bartbunting
bartbunting commented on Feb 15, 2012
bartbunting
on Feb 15, 2012
Hi,

I have just pulled the latest version from git and the same issue appears to still be happening.

I have uncommented the debug line in unoconv and it gives the following output if that is helpfull?

unoconv
sysname=posix
platform=darwin
python=/usr/bin/python
python-version=2.7.1 (r271:86832, Jul 31 2011, 19:30:53)
[GCC 4.2.1 (Based on Apple Inc. build 5658) (LLVM build 2335.15.00)]
URE_BOOTSTRAP=vnd.sun.star.pathname:/Applications/LibreOffice.app/Contents/program/fundamentalrc
UNO_PATH=/Applications/LibreOffice.app/Contents/basis-link/program
PATH=/Applications/LibreOffice.app/Contents/program:/usr/local/Cellar/autoconf/2.68/bin/:/Users/bart/.rvm/gems/ruby-1.9.2-p290/bin:/Users/bart/.rvm/gems/ruby-1.9.2-p290@global/bin:/Users/bart/.rvm/rubies/ruby-1.9.2-p290/bin:/Users/bart/.rvm/bin:/Users/bart/bin:/usr/local/sbin:/usr/local/bin:/usr/local/texlive/2010/bin/universal-darwin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/local/sbin:/opt/local/bin:/usr/local/mysql/bin:/Library/Application Support/VMware Fusion
LD_LIBRARY_PATH=/Applications/LibreOffice.app/Contents/basis-link/program:/Applications/LibreOffice.app/Contents/basis-link/ure-link/lib
unoconv: Cannot find a suitable pyuno library and python binary combination in /Applications/LibreOffice.app/Contents
ERROR: Please locate this library and send your feedback to:
http://github.com/dagwieers/unoconv/issues
No module named uno
unoconv: Cannot find a suitable office installation on your system.
ERROR: Please locate your office installation and send your feedback to:
http://github.com/dagwieers/unoconv/issues

I also tried a simple script with just

import uno, unohelper

This fails because it can't find unohelper. It however works if I just have import uno.

I'm not familiar enough with python to know how to ask where it's finding uno though.

Anything else I can do to help debug?

dagwieers
dagwieers commented on Feb 16, 2012
dagwieers
on Feb 16, 2012
Member
What worries me is that the output says: No module named uno

Also, the PATH still mentions /Applications/LibreOffice.app/Contents/program instead of /Applications/LibreOffice.app/Contents/MacOS, I thought I fixed that ? Are you sure soffice.bin is not inside /Applications/LibreOffice.app/Contents/program ? Maybe it is in 2 locations ?

By default (if you do not modify the path(s), it will look inside the normal search path for python libraries, I don't know what that is on MacOSX. If it can load the uno python module, it finds it there.

Normally there are 2 possibilities:

The LibreOffice installation comes with the (Linux) distribution, in this case using the distribution python is fine, and the python UNO bindings are installed in the normal location for python libraries
The LibreOffice installation comes from upstream (or a third party), in this case it is usually installed in /opt or /usr/local and it ships with its own python interpreter and the bindings are in /opt or in /usr/local. In this case we have to switch from the distribution python (which is invoked by unoconv) to the LibreOffice python using a module search path in the LibreOffice installation path.
Your case seems to:

lack a LibreOffice python binary
does ship with the UNO bindings in the LibreOffice installation path
also has the UNO bindings in the normal python search path, but lacking unohelper
I think the best course of action for me is to get rid of the dependency on unohelper, it's only needed for a few things, and I wonder if I can avoid needing it ? I do not understand how this is supposed to work on MacOSX though, I cannot believe the installation would be crippled to a point where the UNO bindings do not work. The most basic case is indeed starting python and import uno and import unohelper, when that works invoke soffice.bin as a listener. But the first part already fails...

bartbunting
bartbunting commented on Feb 16, 2012
bartbunting
on Feb 16, 2012
Hi,

Here are the contents of the directories in question:

Maybe it gives a clew:

bart@bit:/Applications/LibreOffice.app/Contents$ls -1
Info.plist
Library
MacOS
PkgInfo
Resources
basis-link
program
share
bart@bit:/Applications/LibreOffice.app/Contents$cd MacOS
bart@bit:/Applications/LibreOffice.app/Contents/MacOS$ls -1
about.png
bootstraprc
fundamentalrc
intro.png
sbase
scalc
sdraw
services.rdb
setuprc
shell
simpress
smath
soffice
soffice.bin
sofficerc
swriter
testtool
unoinfo
unopkg
unopkg.bin
urelibs
versionrc
bart@bit:/Applications/LibreOffice.app/Contents/MacOS$

dagwieers
dagwieers commented on Feb 16, 2012
dagwieers
on Feb 16, 2012
Member
Can you send me the output of find /Applications/LibreOffice.app/Contents by email ? Please also send me the output of find / -name "*uno.*". Both will give me a broader view of the installation of LibreOffice and potential UNO libraries :)

Thanks in advance !

dagwieers
dagwieers commented on Feb 16, 2012
dagwieers
on Feb 16, 2012
Member
Bart, thanks again for your help. I think I nailed it, and know why it failed to work. I used to insert the UNO bindings path into the python search path so that python could import modules from the LibreOffice path. After improving unoconv and allowing to replace the python interpreter in memory with the LibreOffice python interpreter, being smart as I am, I removed the part that inserted this library-path because the LibreOffice python is compiled by default to hold this path in the search path.

But of course, this totally neglected your use-case (which I assumed was no longer needed) where the system python interpreter is used with the LibreOffice-provided UNO bindings. This should be fixed thanks to the following commit: 90db481

Can you test again ? Thanks !

sotis
sotis commented on Feb 16, 2012
sotis
on Feb 16, 2012
Author
Sorry for disappearing guys, it has been a hell of a day for me yesterday.

Dag, the path /Applications/LibreOffice.app/Contents/program DOES exist! in fact 'program' is a symbolic link to 'MacOS', so the same content in both locations
I did an ls -laR /Applications/LibreOffice.app/Contents/ as root on my iMac, but I can't submit it from here (I guess there's a size limit for comments?). I can also do the same with my MacBook Air (I have OS X Lion on both machines, but iMac has LibreOffice and MacBook has OpenOffice installed).

How can I send you the listing (if it can actually be of any help)? It's a 589K txt file or a 43K zip file

I can even provide a teamviewer connection to see its behavior live

bartbunting
bartbunting commented on Feb 16, 2012
bartbunting
on Feb 16, 2012
Hi Dag,

Sorry to say it appears not to have worked here :(.

git log HEAD | head
commit bd9bec3
Author: Dag Wieers dag@wieers.com
Date: Thu Feb 16 20:44:44 2012 +0100

- Revert -D / --daemon feature
- Fix disable listener on existing LibreOffice GUI
commit 09f97c8
Merge: 3e9711e a84878d
Author: Dag Wieërs dag@wieers.com
bart@bit:/src/unoconv$./unoconv
unoconv: Cannot find a suitable pyuno library and python binary combination in /Applications/LibreOffice.app/Contents
ERROR: Please locate this library and send your feedback to:
http://github.com/dagwieers/unoconv/issues
No module named uno
unoconv: Cannot find a suitable office installation on your system.
ERROR: Please locate your office installation and send your feedback to:
http://github.com/dagwieers/unoconv/issues
bart@bit:/src/unoconv$

Still the same output.

Kind regards

Bart

bartbunting
bartbunting commented on Feb 20, 2012
bartbunting
on Feb 20, 2012
Hi Dag,

Is there anything further you require from me to debug this issue?

Kind regards

Bart

dagwieers
dagwieers commented on Feb 20, 2012
dagwieers
on Feb 20, 2012
Member
I think it should work, did you try with the latest commits, including: bd9bec3 ?

Otherwise someone will have to understand what is going on, or I will have to find someone with a Mac :-/

bartbunting
bartbunting commented on Feb 20, 2012
bartbunting
on Feb 20, 2012
Hi Dag,

I have tried with the latest version of master. Still no luck.

Is there a way to manually specify the paths? At least that way it may
show that if we find the correct path then everything works. Then it's
just a matter of fixing the detection?

Also, if it helps I could give you access to my laptop to have a go if
that is helpful?

Kind regards

Bart

dagwieers
dagwieers commented on Feb 20, 2012
dagwieers
on Feb 20, 2012
Member
Sure, you can define the various paths just before they are being put in the structure in find_offices(). You can look at the class Office to understand the different arguments (path-names). Assigning values before putting them in an Office object will make unoconv use those. The normal way of setting the Office path is by setting UNO_PATH=/Applications/LibreOffice.app/Contents, but that is not the problem here, because unoconv is looking for some other stuff. (basepath, urepath, unopath, pyuno, binary, python, pythonhome)

I'd rather not access systems remotely.

65 remaining items
gardners
gardners commented on Jul 23, 2012
gardners
on Jul 23, 2012
Super. In the meantime, I have a work around, so all is well.

Paul.

scottprahl
scottprahl commented on Sep 1, 2012
scottprahl
on Sep 1, 2012
There remain two basic issues in unoconv that prevents the mainline from working 'out-of-the-box'

The first is the location of the pyuno binaries and the second is the use of "date --date " in the Makefile. These issues are fixed (in a hopefully cross-platform manner) in a fork https://github.com/scottprahl/unoconv.git that has been merged with the mainline 0.6 as of today.

EDIT: Mainline unoconv works fine now. I deleted my repository to avoid confusion.

dagwieers
dagwieers commented on Sep 2, 2012
dagwieers
on Sep 2, 2012
Member
@scottprahl Is there an easy way to see a diff between your tree and my tree using Github ? Or is this only possible with a squashed pull-request ?

BTW I was wondering if the most simple solution to our problem is to normalize the path (this means replacing symlinks by real paths). I think this works best in all situations and requires no os-specific codepaths. I just commited a new patch that in fact normalizes all paths, the new function abspath() implements a combination of os.path.join() together with os.path.abspath().

Please all, report if this works or not on MacOSX !

dagwieers
dagwieers commented on Sep 2, 2012
dagwieers
on Sep 2, 2012
Member
I am closing this bug as we (once again) assume it to be fixed by commit 00f7f97, if you experience any of the known issues above using the master branch on MacOSX, please reopen this ticket and add more details.

Also, if the current master branch does work for you (out of the box) we would like to know as well.

NOTE: Please use LibreOffice v3.5.6+ or LibreOffice v3.6.0+ as they contain necessary fixes.


dagwieers
closed this as completedon Sep 2, 2012
scottprahl
scottprahl commented on Sep 2, 2012
scottprahl
on Sep 2, 2012
Sorry, still no joy under MacOS :(

The Makefile works perfectly now.

I am currently trying to track down the symlink problem.

scottprahl
scottprahl commented on Sep 2, 2012
scottprahl
on Sep 2, 2012
For what it is worth on MacOS, LibreOffice.app/Contents/program is a symlink to LibreOffice.app/Contents/MacOS (not the other way around). The problem boils down to the fact that launching soffice.bin via

prompt>  /Applications/LibreOffice.app/Contents/MacOS/soffice.bin 
works fine, but

prompt>  /Applications/LibreOffice.app/Contents/program/soffice.bin 
fails with

soffice.bin[18114:707] No Info.plist file in application bundle ...
I don't see another solution than using the /MacOS path directly.


dagwieers
reopened this on Sep 2, 2012
dagwieers
dagwieers commented on Sep 2, 2012
dagwieers
on Sep 2, 2012
Member
The whole point of normalizing the path was to replace symlinks by its real path. I fixed it. Please try again :-/

scottprahl
scottprahl commented on Sep 2, 2012
scottprahl
on Sep 2, 2012
Yep. Somehow I got an intermediate checkin that only had the abspath() function and not the realpath() function. It works fine now. No tweaks needed to the Makefile and the tests run perfectly. Nice work.

dagwieers
dagwieers commented on Sep 2, 2012
dagwieers
on Sep 2, 2012
Member
@scottprahl Yes, my previous commit did not include the realpath() which was in fact what replaces the symlinks. I noticed after your comment that it was still broken. That's also why I renamed that function realpath() as that's what it was supposed to do so more obvious to future contributors.

So thanks specifically to your @scottprahl's care and persistence (and with the help of many others in this thread) we finally nailed it. We are ready to release v0.6 now !


dagwieers
closed this as completedon Sep 2, 2012

shamrin
mentioned this on Apr 24, 2013
unoconv formula Homebrew/legacy-homebrew#12641

dagwieers
added 
MacOS X
 on Apr 23, 2015

amotl
mentioned this on Apr 21, 2018
Support LibreOffice 5.4.6.2 on Mac OS X 10.13.3 with case-sensitive filesystem #447
karaposu
Add a comment
This repository has been archived.
Metadata
Assignees
Labels
LibreOffice
MacOS X
bug
Type
No type
Projects
No projects
Milestone
Relationships
None yet
Development
No branches or pull requests
NotificationsCustomize
You're not receiving notifications from this thread.

Participants
@lloeki
@durandom
@sfermigier
@peterbat
@dagwieers
Issue actions
Footer
© 2026 GitHub, Inc.
Footer navigation
Terms
Privacy
Security
Status
Community
Docs
Contact
Manage cookies
Do not share my personal information
