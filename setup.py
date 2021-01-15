from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
   name='meet_accountmanager',
   version='0.0.1',
   description='A useful module',
   license='Apache 2',
   long_description=long_description,
   author='Man Foo',
   author_email='foomail@foo.com',
   url='https://github.com/publiccodenet/wikimedia-meet-accountmanager',
   packages=['meet_accountmanager'],  #same as name
   install_requires=['Flask', 'requests', 'gunicorn'], #external packages as dependencies
   scripts=[]
)