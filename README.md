# Description

Download all files from a category and its subcategories from the Wikimedia Commons and save them flatly in the current working directory.

# Dependency

`requests`, which is virtually ubiquitous.

# Warning

This script downloads files with up to 32 threads. If there are too many videos or other large files, you might get an OOM exception.
