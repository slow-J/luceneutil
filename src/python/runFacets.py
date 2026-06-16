#!/usr/bin/env python

# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import os

import competition

# Script to compare performance of sandbox and main facets modules
if __name__ == "__main__":
  parser = argparse.ArgumentParser(prog="Local Benchmark Run", description="Run a local benchmark on provided source dataset.")
  parser.add_argument("-s", "-source", "--source", help="Data source to run the benchmark on.")
  parser.add_argument("-searchConcurrency", "--searchConcurrency", default="-1", type=int, help="Search concurrency, 0 for disabled, -1 for using all cores")
  parser.add_argument("-l", "--lucene-dir", help="Baseline lucene checkout")
  parser.add_argument("-c", "--candidate-dir", help="Candidate lucene checkout (same commit as baseline + the change under test)")
  args = parser.parse_args()
  print("Running benchmarks with the following args: %s" % args)

  sourceData = competition.sourceData(args.source)
  countsAreCorrect = args.searchConcurrency != 0
  # enable groupByCat and increase taskRepeatCount to limit time when tasks from different categories
  # are running at the same time and compete for searcher thread pool
  comp = competition.Competition(verifyCounts=not countsAreCorrect, groupByCat=True, taskRepeatCount=200)

  index = comp.newIndex(
    args.lucene_dir,
    sourceData,
    addDVFields=True,
    addDVSkippers=True,  # index lastMod_skipper with a skip index (GITHUB#16249)
    indexSort="lastMod_skipper:long",
    useCMS=True,
    mergePolicy="TieredMergePolicy",
    facets=(
      ("taxonomy:Date", "Date"),
      ("taxonomy:Month", "Month"),
      ("taxonomy:DayOfYear", "DayOfYear"),
      ("sortedset:Date", "Date"),
      ("sortedset:Month", "Month"),
      ("sortedset:DayOfYear", "DayOfYear"),
      ("taxonomy:RandomLabel", "RandomLabel"),
      ("sortedset:RandomLabel", "RandomLabel"),
    ),
  )
  # baseline vs candidate, both during-collection: only the candidate's skipper change differs
  comp.competitor("baseline", args.lucene_dir, index=index, searchConcurrency=args.searchConcurrency, testContext="facetMode:DURING_COLLECTION", pk=False)
  comp.competitor("candidate", args.candidate_dir, index=index, searchConcurrency=args.searchConcurrency, testContext="facetMode:DURING_COLLECTION", pk=False)

  comp.benchmark("facet_implementations")
