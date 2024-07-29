# Introduction

Your personal wakeel assistant to help you research your case

# Getting Started

First clone the repository from Github and switch to the new directory:

    $ git clone https://github.com/megaverse-work/yourwakeel_be.git
    $ cd yourwakeel_be

# Usage

To setup this project:

Assuming you have python3 installed.

### Existing virtual enviornment

Activate virtual enviornment

    $ source myVenv/bin/activate

To install all of the required dependencies

    $ pip install -r requirements.txt

### No virtual enviornment

To make new virtual enviornment

    $ python<version> -m venv <virtual-environment-name>

for example:

    $ python3 -m venv myVenv

Activate virtual enviornment

    $ source myVenv/bin/activate

### Starting the project

Simply apply the migrations:

    $ python manage.py migrate

You can now run the development server:

    $ python manage.py runserver
