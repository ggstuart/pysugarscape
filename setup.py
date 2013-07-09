from setuptools import setup

try:
    import pygtk
except ImportError:
    print 'You need to install pyGTK to use this'
    exit()

def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='pysugarscape',
    version='0.1.0',
    description="A simple agent-based implementation of Epstein & Axtell's sugarscape model.",
    long_description=readme(),
    keywords='agent based Sugarscape',
    author='Graeme Stuart',
    author_email='ggstuart@gmail.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python :: 2.7',
        'Environment :: X11 Applications :: GTK',
    ],
    license='LICENSE.txt',
    install_requires=[
        'pyagents'
    ],
    packages=[
        'pysugarscape'
    ],
    url='https://github.com/ggstuart/pysugarscape.git',
    entry_points = {
        'console_scripts': [
            'pysugarscape_console=pysugarscape.model:main',
            'pysugarscape_gui=pysugarscape.GUI:main'
        ],
    }
)
