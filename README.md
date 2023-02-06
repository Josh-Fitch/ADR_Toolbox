# adr_toolbox
Toolbox of capabilities for the early-stage design and analysis of Active Debris Removal missions, systems, and SoS architectures.

## Authors
- Joshua Fitch -- https://github.com/Josh-Fitch
- Email: jfitch007@outlook.com
- Developed as a part of Purdue AAE MS Thesis ([INSERT LINK TO THESIS])

## Installation
- Git clone this repository to your local machine
- Install the repo as a library using pip
```bash
  pip install -e [adr_toolbox CLONE FILE PATH]
```
- The use of -e will ensure updates to the adr_toolbox repo are reflected in the library usage
- It is recommended to use a virtual environment like venv or Anaconda to manage dependencies

## Requirements
* numpy

## Subpackages
### Data Acquisition
- Ready-to-use functions to interface with Space-Track (USSF) and DISCOweb (ESA) for object data

### Debris Analysis
- Debris Class to capture and format all critical object data
- Methods for risk analysis and scoring of debris
- Functions for network and grouping analysis of debris
- Plotting of debris spatial and characteristic distributions

### Mission Analysis
- Mission Class to capture orbital transfer schemes
- Methods to estimate delta-V for various types of transfers between objects
- Function to solve TSP for groups of objects

### Spacecraft Design
- Spacecraft Class to capture design metrics of spacecraft
- Methods to estimate bus design and sizing around payload
- Methods to estimate project lifecycle cost for one or multiple spacecraft
