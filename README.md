# Computational Design

This repo contains all my submission for the "Computional Design I" module at the [University of Kassel](https://www.uni-kassel.de/uni/). The seminar was hosted by the chair of Prof. Philipp Eversmann, [EDEK](http://www.uni-kassel.de/fb06/fachgebiete/architektur/edek/home.html).

There were 11 assignments. Every exercise is in its own named folder. There were no strict boundaries for the assignments, only topics – you basically had to make your own tasks for the week.  
Students were expected to submit a self-containing Grasshopper file, and a describing PDF. This repo also holds the code by itself as seperate `.py` files.

All exercises are made with Rhino 6 and should run without any issues.

## On Python

My recommendation is to actually script in VSCode (or any other editor you like for that matter). Use the [Python stubs](https://github.com/mcneel/pythonstubs) provided by McNeel, plus [these](https://github.com/gtalarico/ironpython-stubs), to have access to autocomplete. Then use the `read file` + code input at the Python component in Grasshopper.

Since Rhino heavily works with .NET the suiting Python interpreter is IronPython. Remember, this means **Python 2.7**! So don't be tempted to use any of the cool new stuff. Grasshopper Python _seems_ to do an implicit `from __future__ import *`. However I'm not sure to what extend. `print()` is accepted in any case.

### Cheat sheet
Helpful, if you're a beginner.

<details><summary>Cheat sheet</summary>

- Python strings are immutable!
- ... but Lists, Points, Surfaces, Breps, Meshes… are all _REFERENCE_ Type based:  
`myCopyList = myList` : is **not** copying the contents of one list into the other but actually linking both variables to the same data.  
Use `myCopyList = copy.deepcopy(myList)` instead.
- Class names should start with Uppercase
- `print(sys.path)` to see where Python looks for modules to import right now
- You can append to `sys.path`!
- To get the current file path where GH doc is stored: `file_name = ghenv.Component.OnPingDocument().FilePath`
- See the [`ghpy_helpers`](ghpy_helper.py) file to see how to flatten lists in lists.

#### Slicing
_Slicing, the valuable technique of taking ranges out of lists._  
- `list[:-1]`   whole list but without last item  
- `list[1:]`	start at the second item  
- `list[1::2]`	start with second item, always skip one then  

#### Managing different Python versions
Either 
- [via Miniconda](https://conda.io/docs/user-guide/tasks/manage-python.html)
    * Installing a different python besides the existing one:  
    `conda create -n python36 python=3.6 anaconda`  
    python36 is hereby the environment name, python the package name (which could be any one, like `numpy`)
    * activate by typing `activate envname`
    * check by typing `python --version`
    * use `conda env list` for a list of all installed environments
- or [pipenv](https://pipenv.pypa.io/en/latest/)

</details>

---

## License
All code is released under the [BOML](LICENSE.md).
