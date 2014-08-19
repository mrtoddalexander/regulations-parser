Regulations Parser
==================

[![Build Status](https://travis-ci.org/cfpb/regulations-parser.png)](https://travis-ci.org/cfpb/regulations-parser)
[![Coverage Status](https://coveralls.io/repos/cfpb/regulations-parser/badge.png)](https://coveralls.io/r/cfpb/regulations-parser)

This library/tool parses federal regulations (either plain text or XML) and
much of their associated content. It can write the results to JSON files, an
API, or even a git repository. The parser works hand-in-hand with
regulations-core, and API for hosting the parsed regulations and
regulation-site, a front-end for the data structures generated.

This repository is part of a larger project. To read about it, please see 
[http://cfpb.github.io/eRegulations/](http://cfpb.github.io/eRegulations/).

## Quick Start

Here's an example, using CFPB's regulation H.

1. `git clone https://github.com/cfpb/regulations-parser.git`
1. `cd regulations-parser`
1. `pip install -r requirements.txt`
1. `wget
   http://www.gpo.gov/fdsys/pkg/CFR-2012-title12-vol8/xml/CFR-2012-title12-vol8-part1004.xml`
1. `python build_from.py CFR-2012-title12-vol8-part1004.xml 12 2011-18676 15
   1693`

At the end, you will have new directories for `regulation`, `layer`,
`diff`, and `notice` which would mirror the JSON files sent to the API.

## Features

* Split regulation into paragraph-level chunks
* Create a tree which defines the hierarchical relationship between these
  chunks
* Layer for external citations -- links to Acts, Public Law, etc.
* Layer for graphics -- converting image references into federal register
  urls
* Layer for internal citations -- links between parts of this regulation
* Layer for interpretations -- connecting regulation text to the
  interpretations associated with it
* Layer for key terms -- pseudo headers for certain paragraphs
* Layer for meta info -- custom data (some pulled from federal notices)
* Layer for paragraph markers -- specifying where the initial paragraph
  marker begins and ends for each paragraph
* Layer for section-by-section analysis -- associated analyses (from FR
  notices) with the text they are analyzing
* Layer for table of contents -- a listing of headers
* Layer for terms -- defined terms, including their scope
* Layer for additional formatting, including tables, "notes", code blocks,
  and subscripts
* Build whole versions of the regulation from the changes found in final
  rules
* Create diffs between these versions of the regulations

## Requirements

* lxml (3.2.0) - Used to parse out information XML from the federal register
* pyparsing (1.5.7) - Used to do generic parsing on the plain text
* inflection (0.1.2) - Helps determine pluralization (for terms layer)
* requests (1.2.3) - Client library for writing output to an API
* requests_cache (0.4.4) - *Optional* - Library for caching request results
  (speeds up rebuilding regulations)
* GitPython (0.3.2.RC1) - Allows the regulation to be written as a git repo
* python-constraint (1.2) - Used to determine paragraph depth

If running tests:

* nose (1.2.1) - A pluggable test runner
* mock (1.0.1) - Makes constructing mock objects/functions easy
* coverage (3.6) - Reports on test coverage
* cov-core (1.7) - Needed by coverage
* nose-cov (1.6) - Connects nose to coverage

## API Docs

[Read The Docs](https://regulation-parser.readthedocs.org/en/latest/)

## Installation

### Getting the Code and Development Libs

Download the source code from GitHub (e.g. ```git clone [URL]```)

Make sure the ```libxml``` libraries are present. On Ubuntu/Debian, install
it via

```bash
$ sudo apt-get install libxml2-dev libxslt-dev
```

### Create a virtual environment (optional)

```bash
$ sudo pip install virtualenvwrapper
$ mkvirtualenv parser
```

### Get the required libraries

```bash
$ cd regulations-parser
$ pip install -r requirements.txt
```

### Pull down the regulation text

The parser can generally read either plain-text or XML versions of a
regulation, though the XML version gives much better hints. If you have a
regulation as plain text, make sure to remove any table-of-contents and
superflous lines (e.g. "Link to an amendment" and "Back to Top", which might
appear if copy-pasting from
[e-CFR](http://www.ecfr.gov/cgi-bin/ECFR?page=browse).

A better strategy would be to parse using an XML file. This XML can come
from [annual editions](http://www.gpo.gov/fdsys/browse/collectionCfr.action)
of the regulations, or Federal Register notices, if the notice contains a
reissuance of the whole regulation (e.g. CFPB
[re-issued](https://www.federalregister.gov/articles/xml/201/131/725.xml)
regulation E).


### Run the parser

The syntax is 

```bash
$ python build_from.py regulation.ext title notice_doc_# act_title act_section
```

For example, to match the reissuance above:
```bash
$ python build_from.py 725.xml 12 2013-1725 15 1693
```

Here ```12``` is the CFR title number (in our case, for "Banks and
Banking"), ```2013-1725``` is the last notice used to create this version
(i.e. the last "final rule" which is currently in effect), ```15``` is the
title of "the Act" and ```1693``` is the relevant section. Wherever the
phrase "the Act" is used in the regulation, the external link parser will
treat it as "15 U.S.C. 1693".  The final rule number is used to pull in
section-by-section analyses and deduce which notices were used to create
this version of the regulation. It also helps determine which notices to use
when building additional versions of the regulation. To find the document
number, use the [Federal Register](https://www.federalregister.gov/),
finding the last, effective final rule for your version of the regulation
and copying the document number from the meta data (currently in a table on
the right side).

Running the command will generate four folders, ```regulation```,
```notice```, ``layer`` and possibly ``diff`` in the ```OUTPUT_DIR```
(current directory by default).

If you'd like to write the data to an api instead (most likely, one running
regulations-core), you can set the ```API_BASE``` setting (described below).

### Settings

All of the settings listed in ```settings.py``` can be overridden in a
```local_settings.py``` file. Current settings include:

* ```OUTPUT_DIR``` - a string with the path where the output files should be
  written. Only useful if the JSON files are to be written to disk.
* ```API_BASE``` - a string defining the url root of an API (if the output
  files are to be written to an API instead)
* ```GIT_OUTPUT_DIR``` - a string path which will be used to initialize a
  git repository when writing history
* ```META``` - a dictionary of extra info which will be included in the
  "meta" layer. This is free-form, but could be used for copyright
  information, attributions, etc.
* ```CFR_TITLES``` - array of CFR Title names (used in the meta layer); not
  required as those provided are current
* ```DEFAULT_IMAGE_URL``` - string format used in the graphics layer; not
  required as the default should be adequate 
* ```IGNORE_DEFINITIONS_IN``` - a dictionary mapping CFR part numbers to a
  list of terms that should *not* contain definitions. For example, if
  'state' is a defined term, it may be useful to exclude the phrase 'shall
  state'. Terms associated with the constant, `ALL`, will be ignored in all
  CFR parts parsed.
* ```OVERRIDES_SOURCES``` - a list of python modules (represented via
  string) which should be consulted when determining image urls. Useful if
  the Federal Register versions aren't pretty. Defaults to a `regcontent`
  module.
* ```MACRO_SOURCES``` - a list of python modules (represented via strings)
  which should be consulted if replacing chunks of XML in notices. This is
  more or less deprecated by `LOCAL_XML_PATHS`. Defaults to a `regcontent`
  module.
* ```REGPATCHES_SOURCES``` - a list of python modules (represented via
  strings) which should be consulted when determining changes to regulations
  made in final rules.  Defaults to a `regcontent` module
* ```LOCAL_XML_PATHS``` - a list of paths to search for notices from the
  Federal Register. This directory should match the folder structure of the
  Federal Register. If a notice is present in one of the local paths, that
  file will be used instead of retrieving the file, allowing for local
  edits, etc. to help the parser.

## Building the documentation

For most tweaks, you will simply need to run the Sphinx documentation
builder again.

```
$ pip install Sphinx
$ cd docs
$ make dirhtml
```

The output will be in ```docs/_build/dirhtml```.

If you are adding new modules, you may need to re-run the skeleton build
script first:

```
$ pip install Sphinx
$ sphinx-apidoc -F -o docs regparser/
```

##  Running Tests

As the parser is a complex beast, it has several hundred unit tests to help
catch regressions. To run those tests, make sure you have first added all of
the testing requirements:

```bash
$ pip install -r requirements_test.txt
```

Then, run nose on all of the available unit tests:

```bash
$ nosetests tests/*.py
```

If you'd like a report of test coverage, use the [nose-cov](https://pypi.python.org/pypi/nose-cov) plugin:

```bash
$ nosetests --with-cov --cov-report term-missing --cov regparser tests/*.py
```

Note also that this library is continuously tested via Travis. Pull requests
should rarely be merged unless Travis gives the green light.

## Additional Details

Here, we dive a bit deeper into some of the topics around the parser, so
that you may use it in a production setting.

### Parsing Workflow

The parser first reads the file passed to it as a parameter and attempts to
parse that into a structured tree of subparts, sections, paragraphs, etc.
Following this, it will make a call to the Federal Register's API,
retrieving a list of final rules (i.e. changes) that apply this is
regulation. It then writes/saves parsed versions of those notices.

If this all worked well, we save the the parsed regulation and then generate
an save all of the layers associated with it's version. We then generate
additional, whole regulation trees and their associated layers for each
final rule (i.e. each alteration to the regulation).

At the very end, we take all versions of the regulation we've build and
compare each pair (both going forwards and backwards). These diffs are
generated and then written to the API/filesystem/Git.

### Output

The parser has three options for what it does with the parsed documents it
creates. With no configuration, all of the objects it creates will be
pretty-printed as json files and stored in subfolders of the current
directory. Where the output is written can be configured via the
`OUTPUT_DIR` setting. Spitting out JSON files this way is a good way to
track how tweaks to the parser might have unexpected affects on the output
-- just diff two such directories.

If the `API_BASE` setting is configured, the output will be written to an API
(running `regulations-core`) rather than the file system. The same JSON
files are sent to the API as in the above method. This would be the method
used once you are comfortable with the results (by testing the filesystem
output).

A final method, a bit divergent from the other two, is to write the results
as a git repository. Using the `GIT_OUTPUT_DIR` setting, you can tell the
parser to write the versions of the regulation (*only*; layers, notices,
etc. are not written) as a git history. Each node in the parse tree will be
written as a markdown file, with hierarchical information encoded in
directories. This is an experimental feature, but has a great deal of
potential.

### Modifying Data

Our sources of data, through human and technical error, often contain
problems for our parser. Over the parser's development, we've created
several not-always-exclusive solutions. We have found that, in most cases,
the easiest fix is to download and edit a *local* version of the problematic XML. Only if there's some complication in that method should you progress to the more complex strategies.

All of the paths listed in `LOCAL_XML_PATHS` are checked when fetching
regulation notices. The file/directory names in these folders should mirror
those found on federalregister.gov, (e.g. articles/xml/201/131/725.xml). Any
changes you make to these documents (such as correcting XML tags, rewording
amendment paragraphs, etc.) will be used as if they came from the Federal
Register.

In addition, certain notices have *multiple* effective dates, meaning that
different parts of the notice go into effect at different times. This
complication is not handled automatically by the parser. Instead, you must
manually copy the notice into two (or more) versions, such that 503.xml
becomes 503-1.xml, 503-2.xml, etc. Each file must then be *manually*
modified to change the effective date and remove sections that are not
relevant to this date. We sometimes refer to this as "splitting" the notice.

While editing the notice is generally an effective strategy, there are
certain corner cases in which the parser simply does not support the logic
needed to determine what's going on. In these situations, you have the
option of using custom "patches" for notices, via the `REGPATCHES_SOURCES`
setting. The setting refers to a Python object that has keys and values
(e.g. a `dict`). The keys are notice document numbers (e.g. 2013-22752 or
2013-22752_20140110 for a split notice). When the changes associated with a
particular notice are consulted (to build the next regulation version), the
entries in the value are added to the list of notice `changes`. This
strategy is useful for certain appendix alterations.

### Appendix Parsing

The most complicated segments of a regulation are their appendices, at least
from a structural parsing perspective. This is because appendices are
free-form, often with unique variations on sub-sections, headings, paragraph
marker hierarchy, etc. Given all this, the parser does it's best job to
determine *an* ordering and *a* hierarchy for the subsections/paragraphs
contained within an appendix.

In general, if the parser can find a unique identifier or paragraph marker,
it will note the paragraph/section accordingly. So "Part I: Blah Blah"
becomes 1111-A-I, and "a. Some text" and "(a) Some text)" might become
1111-A-I-a. When the citable value of a paragraph cannot be determined (i.e.
it has no paragraph marker), the paragraph will be assigned a number and
prefaced with "p" (e.g. p1, p2). Similarly, headers become h1, h2, ...

This works out, but had numerous downsides. Most notably, as the citation
for such paragraphs is arbitrary, determining changes to appendices is quite
difficult (often requiring patches). Further, without guidance from
paragraph markers/headers, the parser must make assumptions about the
hierarchy of paragraphs. It currently uses some heuristics, such as headers
indicating a new depth level, but is not always accurate.

### Markdown/Plaintext-ifying

With some exceptions, we treat a plain-text version of the regulation as
cannon. By this, we mean that the *words* of the regulation could for much
more than their presentation in the source documents. This allows us to
build better tables of content, export data in more formats, and the other
niceties associated with separating data from presentation.

At points, however, we need to encode non-plain text concepts into the
plain-text regulation. These include displaying images, tables, offsetting
blocks of text, and subscripting. To encode these concepts, we use a
variation of Markdown. 

Images become 

```
![Appendix A9](ER27DE11.000)
```

Tables become

```
| Header 1 | Header 2|
---
| Cell 1, 1 | Cell 1, 2 |
```

Subscripts become

```
P_{0}
```

etc.

### Runtime

A quick note of warning: the parser was not optimized for speed. It performs
many actions over and over, which can be *very* slow on very large
regulations (such as CFPB's regulation Z). Further, regulations that have
been amended a great deal cause further slow down, particularly when
generating diffs (currently an n**2 operation). Generally, parsing will take
less than ten minutes, but in the extreme example of reg Z, it currently
requires several hours.
