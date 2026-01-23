2024-03-28 16:10:50
Zamboniman
Member
Registered: 2010-06-20
Posts: 17
I have a python script that uses the uno bridge to fill in various fields in a libreoffice calc document. This has worked very well for a long time. After an update last week it no longer works.

The first issue was that it complained about python not being able to import uno. Okay, not sure why that wasn't an issue before but it is now, but adding 'export PYTHONPATH=$PYTHONPATH:/usr/lib/libreoffice/program/' seemed to fix this. However, not really. This led to a different problem.

Now the script errors out with:

desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx) uno.com.sun.star.uno.RuntimeException: Binary URP bridge disposed during call at /usr/src/debug/libreoffice-fresh/libreoffice-24.2.1.2/binaryurp/source/bridge.cxx:615

Oddly, I don't think either libreoffice nor python were updated during that pacman update. Nonetheless, it doesn't work now, and seems to be uno crashing.

Does anybody have any ideas for where to start? I do not know enough about python and uno to know where to go from here.

Last edited by Zamboniman (2024-04-02 17:23:44)

Offline

#22024-04-02 17:18:54
Zamboniman
Member
Registered: 2010-06-20
Posts: 17
Solved it.

Something clearly changed in either libreoffice or python, which resulted in a slightly different environment. Some checking showed unoconv still worked, which was confusing since it leverages the same functionality. So, checking the source of unoconv showed some interesting environment setup, which I copied.

So, adding:

# For bookingapp script uno setup added 2024-04-01
export PATH=$PATH:/usr/lib/libreoffice/program
export URE_BOOTSTRAP=vnd.sun.star.pathname:/usr/lib/libreoffice/program/fundamentalrc
export UNO_PATH=/usr/lib/libreoffice/program
export LD_LIBRARY_PATH=/usr/lib/libreoffice/program:/usr/lib/libreoffice/ure/lib
export PYTHONPATH=/usr/lib/libreoffice/program/:$PYTHONPATH

to my .bashrc did the trick and this now works perfectly once again.

I thought I'd post this solution here just in case anybody else ran across this issue. This is now solved.