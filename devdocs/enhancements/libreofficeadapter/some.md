Skip to main content
Stack Overflow
About

Products
For Teams
Search…
Home
Questions
AI Assist
Tags
Challenges
Chat
Articles
Users
Companies
Collectives
Communities for your favorite technologies. Explore all Collectives

Stack Internal
Stack Overflow for Teams is now called Stack Internal. Bring the best of human thought and AI automation together at your work.

 
Installing pyuno (LibreOffice) for private Python build
Asked 12 years, 10 months ago
Modified 6 years, 1 month ago
Viewed 8k times
5

There are a few related threads about this topic here ad here but they seem a bit dated.

I just downloaded LibreOffice 4 which has a Python 3.3.0 built in. Using that Python I can import and use UNO just fine, and control Office from my Python script. However, many of my other modules are missing from that Python—and UNO is the only one missing from my Python.

Is there any way that I can install pyuno for my local Python? The LibreOffice source tree includes a pyuno/ source tree, but I'm not sure how to go about building/integrating this into another Python tree.

Any experiences here? Help? Hints? Dos, Don'ts, Dohs?

EDIT The answer below works just fine for Linux, and I have no problem there extending the PYTHONPATH to import uno. Matters are different on the Mac, so take a look at the other answer.

EDIT Absolutely take this anwer into consideration when tinkering with Python paths!

pythonlibreofficeuno
Share
Improve this question
Follow
edited May 23, 2017 at 12:16
Community's user avatar
CommunityBot
111 silver badge
asked Mar 5, 2013 at 11:58
Jens's user avatar
Jens
9,30699 gold badges6565 silver badges8484 bronze badges
I have LibreOffice 4 in Ubuntu 13.04, but Python is not mentioned in any Tools-Macro submenu. Do you have it in yours? – 
stenci
 CommentedJul 29, 2013 at 3:29
Not sure about Ubuntu, but on my Mac the python interpreter is part of the package in /Applications/LibreOffice.app/Contents/MacOS. The UNO wrapper lives in that same folder. It all came as part of the LibreOffice package. – 
Jens
 CommentedJul 29, 2013 at 9:48
Related: stackoverflow.com/questions/24965406/… – 
Jens
 CommentedOct 9, 2014 at 11:26
Add a comment
4 Answers
Sorted by:

Highest score (default)
4

Once you try to run PyUNO off any other python executable than the one provided with LO, things do get rough.

The SEGV on Mac is because LO's libpyuno.dylib (loaded via libuno.dylib, which in turn is loaded via "import uno") references @loader_path/LibreOfficePython.framework/Versions/3.3/LibreOfficePython (run "otool -L" on that file; path as on current LO master; paths are a little different on various LO versions). When run from a different python process than LO's, that means there'll be two python runtimes in the process (and the LO one not even properly initialized, probably), and that leads to a SEGV somewhere in that LibreOfficePython. (This happens to work better on Linux, where libpyuno.so references libpython3.3m.so, and normally finds the LO python one's next to itself via its RPATH, but if any libpython3.3m.so happens to already be loaded into the process (from the other python), the Linux loader happily re-uses that one.)

One gross hack on Mac is to use install_name_tool to "rewire" libpyuno.dylib to reference the other python's Python.framework/Versions/3.3/Python (by absolute path) instead of @loader_path/LibreOfficePython.framework/Versions/3.3/LibreOfficePython.

Another gotcha is that LO's python (on Linux and Mac) is actually a shell script around the true python executable. It needs to set up a number of env vars (whose purpose is even documented in the script). To make PyUNO work from a different python you'll want to set up these env vars too, esp. UNO_PATH, URE_BOOTSTRAP, and the parts of PYTHONPATH that find the LO-specific libs (rather than those that come with python itself). Note that the details of those env vars' values differ among LO versions.

Share
Improve this answer
Follow
answered Feb 18, 2015 at 20:36
Stephan Bergmann's user avatar
Stephan Bergmann
18111 silver badge55 bronze badges
Sign up to request clarification or add additional context in comments.

4 Comments


Jens
Over a year ago
Are you saying that it was sheer dumb luck that import uno worked on Linux? If that is correct, then it sounds like it is better to use the LO Python and set up a venv around that one?

Stephan Bergmann
Over a year ago
Yes, by luck. PyUNO is not designed to work with an arbitrary python installation (it's already tricky enough to have everything working with LO's own python). And yes, if you have a choice which python to use, it is most likely easier to stick to the LO one.

Jens
Over a year ago
Considering that LO ships with Python only and without any other Python tools, it seems that following this guide is the way to go about setting up a virtual environment around LO's Python?

Lloeki
Over a year ago
It wasn't luck if you're using the distro's packaged LibreOffice as it's typically built against and using the distro provided python. At least it is so on Debian 9: apt-get install -y libreoffice; python3  -c 'import uno; print(uno)'.
Add a comment
2

It is a late answer and I don't have the exact same setup as you have, but for me, I could simply adjust PYTHONPATH so that the directory where uno.py lives is known to python.

bash> export PYTHONPATH=${PYTHONPATH}:/usr/lib/libreoffice/program
bash> python
>>> import uno
A requirement is that your LibreOffice/OO python has the same version as your regular one: Python will compile the .py to .pyc, and that format is not transferable between versions (at least, that is not guaranteed).

Do a locate uno.py if you are not sure where your file is. Inspecting where /usr/bin/libreoffice links to may also help.

Share
Improve this answer
Follow
answered Oct 3, 2013 at 11:54
dirkjot's user avatar
dirkjot
3,78411 gold badge2727 silver badges1818 bronze badges
2 Comments


Jens
Over a year ago
This works fine on Linux, and I am even able to mix Py 3.3 and Py 3.4. (Perhaps I'm walking on thin ice, but it has worked so far :-))

Jens
Over a year ago
Yes, I was walking on thin ice and it broke. Don't mix Python versions!
1

I recently wanted to use pyuno with django (i.e. I had a pricing engine in a spreadsheet and the django app opened it up, filled in user input, and retrieved the price after recalculating). The only reasonable solution to this is either use docker containers or a linux vm on whatever platform you're working on (I'm on mac and use parallels for ubuntu machine). Any other solution is a colossal waste of time.

When you're in the linux environment, all you have to do is run apt-get install python3-uno and set your python path to $PYTHONPATH:/usr/lib/python3/dist-packages/ (i.e. where apt-get installs python3-uno and everything will be ok (only in linux environment).

Share
Improve this answer
Follow
answered Dec 5, 2019 at 4:22
Ben's user avatar
Ben
1,09288 silver badges1919 bronze badges
1 Comment


Timothy C. Quinn
Over a year ago
Worked for me. FYI for others, after installing python3-uno to find the dist-packages folder, use: dpkg-query -L python3-uno | grep uno.py
0

Linux

dirkjot's answer to this thread works great on Linux.

Mac (Yosemite)

Things are a little bit more tricky here, and as of LibreOffice 4.3 I still can't extend my PYTHONPATH to LibreOffice and import uno without crashing on Mac:

localhost ~ > PYTHONPATH=$PYTHONPATH:/Applications/LibreOffice64.app/Contents/MacOS python3.3
Python 3.3.6 (default, Nov 12 2014, 18:18:46) 
[GCC 4.2.1 Compatible Apple LLVM 6.0 (clang-600.0.54)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import uno
Segmentation fault: 11
But here is what works for me. First, I have to make sure that both Python and my LibreOffice are built for 32b or 64b; they can't be mixed. I'm working with 64b MacPorts Python 3.3 and 64b LibreOffice for Mac (download link) which comes with Python 3.3. Second, I have to make sure to run the right Python and extend the PYTHONPATH correctly. Because I can't run my MacPorts Python and extend it with LibreOffice's path, I have to do it the other way around: run the LibreOffice Python and extend it with my MacPorts Python path:

localhost ~ > PYTHONPATH=$PYTHONPATH:/opt/local/Library/Frameworks/Python.framework/Versions/3.3/lib/python3.3/site-packages /Applications/LibreOffice64.app/Contents/MacOS/python
Python 3.3.5 (default, Dec 12 2014, 10:33:58) 
[GCC 4.2.1 Compatible Apple LLVM 6.0 (clang-600.0.51)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import uno
>>> import lxml
>>> 
Note how uno is imported from the LibreOffice's Python path, and lxml lives in MacPort's Python path.

Share
Improve this answer
Follow
edited May 23, 2017 at 12:33
Community's user avatar
CommunityBot
111 silver badge
answered Jan 16, 2015 at 1:05
Jens's user avatar
Jens
9,30699 gold badges6565 silver badges8484 bronze badges
1 Comment


dirkjot
Over a year ago
Clever solution. As a minor comment, I would always extend PYTHONPATH, not set it as you do. You will break something one day, when you least expect it.
Your Answer
 

  
Sign up or log in
Post as a guest
Name
Email
Required, but never shown

By clicking “Post Your Answer”, you agree to our terms of service and acknowledge you have read our privacy policy.

Start asking to get answers

Find the answer to your question by asking.

Explore related questions

pythonlibreofficeuno
See similar questions with these tags.

The Overflow Blog
How Stack Overflow is taking on spam and bad actors
How AWS re:Invented the cloud
Featured on Meta
Community Asks Sprint Announcement – January 2026: Custom site-specific badges!
All users on Stack Overflow can now participate in chat
Should Stack Overflow utilize machine learning anti-spam?
Community activity
Last 1 hr
Users online activity
6542 users online
 18 questions
 10 answers
 45 comments
 159 upvotes
Popular tags

rust
excel
pull-request
javascript
csv
c++
Popular unanswered question

Is it possible to force template reevaluation prior to C++20?
c++
c++17
template-meta-programming
User avatar
Sergey Kolesnik
4.1k
1,075 days ago
Linked
11
How do you install or activate PyUno in LibreOffice?
6
Getting python to import uno / pyuno
3
Using pyuno with my existing python installation
3
ModuleNotFoundError: No module named 'uno'
1
Connecting to LO from python IDE with PyUNO for debugging
Related
7
OpenOffice.org development with pyUno for Windows—which Python?
2
Using PyUNO on Windows and CentOS
2
Openoffice3.1 pyuno confusing errors
6
Loading a document on OpenOffice using an external Python program
3
Using pyuno with my existing python installation
11
How do you install or activate PyUno in LibreOffice?
0
Using pyUno to write text into Libre/OpenOffice Writer
4
running PyUNO in django
6
Getting python to import uno / pyuno
1
can't import uno in python for libreoffice on ubuntu 16.04
Hot Network Questions
Term for Voltage Regulator which absorbs downstream spikes?
Domestic pure math PhD applicants with risky profile - any other options to consider?
Are U.S. federal officials required to identify themselves when entering a fenced area of a home to make an arrest?
Fill In The Blank To Get Four Words
Using self-translated foreign text possibly out of copyright?
Set xmp description for other languages too
Are there stats available for Omen Dogs?
Tabs in the insert option of sed command
Killer sudoku: Solve for X
Why Cournot and not always Bertrand?
Weird summation
Which is preferred nowadays: 纹身 vs. 文身?
How to say "spicy" in Latin?
How would advanced aliens achieve quick homo sapiens sapiens extinction on Earth, given their goal to not hinder future sapients evolution on Earth?
Phrase/word for person who eats anything without complaint
Is working on and publishing "grunt math" acceptable as a high school student?
How can an antenna that is only 1 m long receive AM radio with a wavelength of 281 meters?
Damage reduction for (DR/ X OR Y) and (DR/X AND Y) and (DR/x AND DR/Y)
LaTeX macro to generate a centered grid of subfigures from a comma list (no gaps, equal widths, auto sublabels 1,2,3…)
Replace atom in large protein structure
Primes in Latex
How do 'sudo' permission bits influence (e)uid and (e)gid?
Difference between BJT and FET current mirror
Intuition behind likelihood. Multinomial distribution
 Question feed







Stack Overflow
Questions
Help
Chat
Business
Stack Internal
Stack Data Licensing
Stack Ads
Company
About
Press
Work Here
Legal
Privacy Policy
Terms of Service
Contact Us
Cookie Settings
Cookie Policy
Stack Exchange Network
Technology
Culture & recreation
Life & arts
Science
Professional
Business
API
Data
Blog
Facebook
Twitter
LinkedIn
Instagram
Site design / logo © 2026 Stack Exchange Inc; user contributions licensed under CC BY-SA . rev 2026.1.14.38635