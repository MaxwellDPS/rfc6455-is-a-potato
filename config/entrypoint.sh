#!/bin/bash

hypercorn tailproxy:app -b 0.0.0.0:6969 --keep-alive 0