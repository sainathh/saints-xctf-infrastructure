### Overview

This is the testing suite for the SaintsXCTF cloud infrastructure.  Tests are run in Python using Amazon's boto3 module.  
Each infrastructure grouping has its own test suite.  Each test suite contains many individual tests.  Test suites can 
be run independently or all at once.

To run all test suites at once, execute the following command from this directory:

```
./masterTestSuite.py
```

To run a single test suite, navigate to the suite's directory and execute the file following the regular expression  
`^[a-z]+TestSuite.py$`.

### Files

| Filename             | Description                                                                                  |
|----------------------|----------------------------------------------------------------------------------------------|
| `bastion/`           | Test suite for the Bastion host.                                                             |
| `masterTestFuncs.py` | Functions used to help create a test suite environment.                                      |
| `masterTestSuite.py` | Invokes all the test suites.                                                                 |
| `setup.sh`           | Bash script to setup the environment for a test suite.                                       |