#!/usr/bin/env python
# -*- coding: utf-8

from pstats import Stats


if __name__ == "__main__":
    s = Stats("stats.profile")
    s.sort_stats("tottime")
    s.print_stats(20)
