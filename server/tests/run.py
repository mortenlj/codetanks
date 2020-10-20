#!/usr/bin/env python

import os
import pytest
import sys

if __name__ == "__main__":
    package = sys.argv[1]
    test_file = sys.argv[2]
    args = sys.argv[3:]
    test_path = os.path.join(package, test_file)
    ret_code = pytest.main([test_path] + args)
    sys.exit(ret_code)
