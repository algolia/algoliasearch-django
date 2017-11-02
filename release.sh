#!/bin/sh
rm -f dist/* # Remove eventual previous versions
python setup.py sdist bdist_wheel # Create Source Distribution and Universal Wheel
twine upload dist/* # Upload to PyPI

