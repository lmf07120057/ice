#!/usr/bin/env python
# **********************************************************************
#
# Copyright (c) 2003-2007 ZeroC, Inc. All rights reserved.
#
# This copy of Ice is licensed to you under the terms described in the
# ICEE_LICENSE file included in this distribution.
#
# **********************************************************************

import os, sys, shutil, fnmatch, re, glob

#
# Program usage.
#
def usage():
    print "Usage: " + sys.argv[0] + " [options] [tag]"
    print
    print "Options:"
    print "-h    Show this message."
    print "-v    Be verbose."
    print
    print "If no tag is specified, HEAD is used."

#
# Find files matching a pattern.
#
def find(path, patt):
    result = [ ]
    files = os.listdir(path)
    for x in files:
        fullpath = os.path.join(path, x);
        if os.path.isdir(fullpath) and not os.path.islink(fullpath):
            result.extend(find(fullpath, patt))
        elif fnmatch.fnmatch(x, patt):
            result.append(fullpath)
    return result

#
# Comment out rules in a Makefile.
#
def fixMakefile(file, target):
    origfile = file + ".orig"
    os.rename(file, origfile)
    oldMakefile = open(origfile, "r")
    newMakefile = open(file, "w")
    origLines = oldMakefile.readlines()

    doComment = 0
    doCheck = 0
    newLines = []
    for x in origLines:
        #
        # If the rule contains the target string, then
        # comment out this rule.
        #
        if not x.startswith("\t") and x.find(target) != -1 and x.find(target + ".o") == -1:
            doComment = 1
        #
        # If the line starts with "clean::", then check
        # the following lines and comment out any that
        # contain the target string.
        #
        elif x.startswith("clean::"):
            doCheck = 1
        #
        # Stop when we encounter an empty line.
        #
        elif len(x.strip()) == 0:
            doComment = 0
            doCheck = 0

        if doComment or (doCheck and x.find(target) != -1):
            x = "#" + x
        newLines.append(x)

    newMakefile.writelines(newLines)
    newMakefile.close()
    oldMakefile.close()
    os.remove(origfile)

#
# Remove lines containing a keyword from a file.
#
def editFile(file, target):
    origfile = file + ".orig"
    os.rename(file, origfile)
    oldFile = open(origfile, "r")
    newFile = open(file, "w")
    origLines = oldFile.readlines()

    newLines = []
    for x in origLines:
        if x.find(target) == -1:
            newLines.append(x)

    newFile.writelines(newLines)
    newFile.close()
    oldFile.close()
    os.remove(origfile)

#
# Comment out rules in VC project.
#
def fixProject(file, target):
    origfile = file + ".orig"
    os.rename(file, origfile)
    oldProject = open(origfile, "r")
    newProject = open(file, "w")
    origLines = oldProject.readlines()

    #
    # Find a Source File declaration containing SOURCE=<target>
    # and comment out the entire declaration.
    #
    expr = re.compile("SOURCE=.*" + target.replace(".", "\\.") + ".*")
    inSource = 0
    doComment = 0
    newLines = []
    source = []
    for x in origLines:
        if x.startswith("# Begin Source File"):
            inSource = 1

        if inSource:
            if not doComment and expr.match(x) != None:
                doComment = 1
            source.append(x)
        else:
            newLines.append(x)

        if x.startswith("# End Source File"):
            inSource = 0
            for s in source:
                if doComment:
                    newLines.append('#xxx#' + s)
                else:
                    newLines.append(s)
            doComment = 0
            source = []

    newProject.writelines(newLines)
    newProject.close()
    oldProject.close()
    os.remove(origfile)

#
# Comment out implicit parser/scanner rules in config/Make.rules.
#
def fixMakeRules(file):
    origfile = file + ".orig"
    os.rename(file, origfile)
    oldFile = open(origfile, "r")
    newFile = open(file, "w")
    origLines = oldFile.readlines()

    doComment = 0
    newLines = []
    for x in origLines:
        if x.find("%.y") != -1 or x.find("%.l") != -1:
            doComment = 1
        #
        # Stop when we encounter an empty line.
        #
        elif len(x.strip()) == 0:
            doComment = 0

        if doComment:
            x = "#" + x
        newLines.append(x)

    newFile.writelines(newLines)
    newFile.close()
    oldFile.close()
    os.remove(origfile)

#
# Fix version in README, INSTALL files
#
def fixVersion(files, version):

    for file in files:
        origfile = file + ".orig"
        os.rename(file, origfile)
        oldFile = open(origfile, "r")
        newFile = open(file, "w")
        newFile.write(re.sub("@ver@", version, oldFile.read()))
        newFile.close()
        oldFile.close()
        os.remove(origfile)

#
# Check arguments
#
tag = "HEAD"
verbose = 0
for x in sys.argv[1:]:
    if x == "-h":
        usage()
        sys.exit(0)
    elif x == "-v":
        verbose = 1
    elif x.startswith("-"):
        print sys.argv[0] + ": unknown option `" + x + "'"
        print
        usage()
        sys.exit(1)
    else:
        tag = x

#
# Remove any existing "dist" directory and create a new one.
#
distdir = "dist"
if os.path.exists(distdir):
    shutil.rmtree(distdir)
os.mkdir(distdir)
os.mkdir(os.path.join(distdir, "icesl"))

#
# Export sources from git.
#
print "Checking out sources " + tag + "..."
if verbose:
    quiet = "-v"
else:
    quiet = ""
os.system("git archive " + quiet + " " + tag + " . | (cd dist/icesl && tar xf -)")

os.chdir(distdir)

#
# Remove files.
#
print "Removing unnecessary files..."
filesToRemove = [ \
    os.path.join("icesl", "allTests.py"), \
    os.path.join("icesl", "makedist.py"), \
    os.path.join("icesl", "config", "TestUtil.py"), \
    os.path.join("icesl", "config", "Make.rules.cs"), \
    os.path.join("icesl", "config", "makeconfig.py"), \
    os.path.join("icesl", "config", "makedepend.py"), \
    os.path.join("icesl", "test", "Makefile.mak"), \
    ]
filesToRemove.extend(find("icesl", ".gitignore"))
filesToRemove.extend(find("icesl", "Makefile"))
for x in filesToRemove:
    os.remove(x)

shutil.rmtree(os.path.join("icesl", "test", "Ice", "proxy"))
shutil.rmtree(os.path.join("icesl", "test", "IceCS"))

#
# Comment out the implicit parser and scanner rules in
# config/Make.rules.
#
#print "Fixing makefiles..."
#fixMakeRules(os.path.join("icesl", "config", "Make.rules"))

#
# Get IceSL version.
#
config = open(os.path.join("icesl", "src", "Ice", "AssemblyInfo.cs"), "r")
version = re.search("AssemblyVersion.*\"([0-9\.]*)\".*", config.read()).group(1)

print "Fixing version in README and INSTALL files..."
fixVersion(find("icesl", "README*"), version)
fixVersion(find("icesl", "INSTALL*"), version)

#
# Create archives.
#
print "Creating distribution..."
iceslver = "IceSL-" + version
os.rename("icesl", iceslver)
if verbose:
    quiet = "v"
else:
    quiet = ""
os.system("tar c" + quiet + "f " + iceslver + ".tar " + iceslver)
os.system("gzip -9 " + iceslver + ".tar")
if verbose:
    quiet = ""
else:
    quiet = "q"
os.system("zip -9r" + quiet + " " + iceslver + ".zip " + iceslver)

#
# Copy files (README, etc.).
#
#shutil.copyfile(os.path.join(iceslver, "CHANGES"), "IceSL-" + version + "-CHANGES")

#
# Done.
#
print "Cleaning up..."
shutil.rmtree(iceslver)
print "Done."
