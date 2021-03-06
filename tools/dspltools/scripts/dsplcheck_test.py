#!/usr/bin/python2
#
# Copyright 2018 Google LLC
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

"""Tests of dsplcheck module."""


__author__ = 'Benjamin Yolken <yolken@google.com>'

import os
import os.path
import re
import shutil
import StringIO
import sys
import tempfile
import unittest
import zipfile

import dsplcheck


_DSPL_CONTENT = (
    """<?xml version="1.0" encoding="UTF-8"?>
<dspl xmlns="http://schemas.google.com/dspl/2010"
    xmlns:time="http://www.google.com/publicdata/dataset/google/time">
  <import namespace="http://www.google.com/publicdata/dataset/google/time"/>
  <info>
    <name>
      <value>Dataset Name</value>
    </name>
  </info>
  <provider>
    <name>
      <value>Provider Name</value>
    </name>
  </provider>
</dspl>""")


_DSPL_CONTENT_BAD_CSV_PATH = (
    """<?xml version="1.0" encoding="UTF-8"?>
<dspl xmlns="http://schemas.google.com/dspl/2010"
    xmlns:time="http://www.google.com/publicdata/dataset/google/time">
  <import namespace="http://www.google.com/publicdata/dataset/google/time"/>
  <info>
    <name>
      <value>Dataset Name</value>
    </name>
  </info>
  <provider>
    <name>
      <value>Provider Name</value>
    </name>
  </provider>
  <tables>
    <table id="my_table">
      <column id="col1" type="string"/>
      <column id="col2" type="string"/>
      <data>
        <file format="csv" encoding="utf-8">non_existent_file.csv</file>
      </data>
    </table>
  </tables>
</dspl>""")


class DSPLCheckTests(unittest.TestCase):
  """Test case for dsplcheck module."""

  def setUp(self):
    self.input_dir = tempfile.mkdtemp()
    self.valid_dspl_file_path = (
        os.path.join(self.input_dir, 'valid_dataset.xml'))

    self.valid_dspl_file = open(
        self.valid_dspl_file_path, 'w')
    self.valid_dspl_file.write(_DSPL_CONTENT)
    self.valid_dspl_file.close()

  def tearDown(self):
    shutil.rmtree(self.input_dir)

  def testValidDataset(self):
    """Test basic case of dataset that validates and parses correctly."""
    self._StdoutTestHelper(
        dsplcheck.main, [self.valid_dspl_file_path],
        'validates successfully.*Parsing completed.*'
        'Checking DSPL model and data.*Completed')

  def testBadXMLFilePath(self):
    """Test case where bad XML file path is passed in."""
    self._StdoutTestHelper(
        dsplcheck.main, ['nonexistent_input_file.xml'],
        'Error opening XML file', expect_exit=True)

  def testBadCSVFilePath(self):
    """Test case where DSPL file has bad CSV reference."""
    bad_csv_dspl_file_path = (
        os.path.join(self.input_dir, 'invalid_csv_dataset.xml'))

    bad_csv_dspl_file = open(bad_csv_dspl_file_path, 'w')
    bad_csv_dspl_file.write(_DSPL_CONTENT_BAD_CSV_PATH)
    bad_csv_dspl_file.close()

    self._StdoutTestHelper(
        dsplcheck.main, [bad_csv_dspl_file_path],
        'Error while trying to parse', expect_exit=True)

  def testSchemaOnlyOption(self):
    """Test that 'schema only' checking level option works correctly."""
    self._StdoutTestHelper(
        dsplcheck.main, [self.valid_dspl_file_path, '-l', 'schema_only'],
        'validates successfully\W*Completed')

  def testSchemaAndModelOption(self):
    """Test that 'schema and model' checking level option works correctly."""
    self._StdoutTestHelper(
        dsplcheck.main, [self.valid_dspl_file_path, '-l', 'schema_and_model'],
        'Checking DSPL model(?! and data)')

  def testZipInput(self):
    """Test that module properly handles zipped input."""
    zip_path = os.path.join(self.input_dir, 'dataset.zip')

    zip_file = zipfile.ZipFile(zip_path, 'w')
    zip_file.write(self.valid_dspl_file_path)
    zip_file.close()

    self._StdoutTestHelper(
        dsplcheck.main, [zip_path],
        'validates successfully.*Parsing completed.*'
        'Checking DSPL model and data.*Completed')

  def testZipMissingXML(self):
    """Test that zip file without an XML file produces error."""
    zip_path = os.path.join(self.input_dir, 'dataset.zip')

    zip_file = zipfile.ZipFile(zip_path, 'w')
    zip_file.writestr('test.txt', 'Text')
    zip_file.close()

    self._StdoutTestHelper(
        dsplcheck.main, [zip_path],
        'does not have any XML', expect_exit=True)

  def testZipMultipleXMLFiles(self):
    """Test that zip file with multiple XML files produces error."""
    zip_path = os.path.join(self.input_dir, 'dataset.zip')

    zip_file = zipfile.ZipFile(zip_path, 'w')
    zip_file.writestr('test.xml', 'Text')
    zip_file.writestr('test2.xml', 'Text')
    zip_file.close()

    self._StdoutTestHelper(
        dsplcheck.main, [zip_path],
        'multiple XML files', expect_exit=True)

  def _StdoutTestHelper(self, function, args,
                        expected_output, expect_exit=False):
    """Check the stdout output of a function against its expected value.

    Args:
      function: A function to execute
      args: The arguments to pass to the function
      expected_output: A regular expression expected to match the stdout output
      expect_exit: Boolean indicating whether the function execution should
                   trigger a system exit
    """
    saved_stdout = sys.stdout

    redirected_output = StringIO.StringIO()
    sys.stdout = redirected_output

    if expect_exit:
      self.assertRaises(SystemExit, function, args)
    else:
      function(args)

    self.assertTrue(
        re.search(expected_output, redirected_output.getvalue(), re.DOTALL))

    redirected_output.close()
    sys.stdout = saved_stdout


if __name__ == '__main__':
  unittest.main()
