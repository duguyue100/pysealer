# This is a Python template Makefile, do modification as you want
#
# Project: PySealer 
# Author: Yuhuang Hu
# Email : duguyue100@gmail.com

HOST = 127.0.0.1
PYTHONPATH="$(shell printenv PYTHONPATH):$(PWD)"

clean:
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
	find . -name '*~' -exec rm --force  {} +

run:

test:
	PYTHONPATH=$(PYTHONPATH) python 

io-test:
	PYTHONPATH=$(PYTHONPATH) python ./pysealer/test_script/io_test.py 

cleanall:
