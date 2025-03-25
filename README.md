# CAP Orientation Flight Points Calculator

A Python tool for managing Civil Air Patrol (CAP) cadet orientation flight assignments. This tool calculates priority points based on flight history and creates prioritized flight slot assignments.

## Features

- **Points Calculation**: Assigns points to cadets based on:
  - Number of remaining powered flights needed
  - Time since last flight
  - Special consideration for cadets with no previous flights
- **Slot Assignment**: Creates prioritized lists of:
  - Primary slots (specified number of highest-point cadets)
  - Alternates (remaining cadets)
  - Identifies any unmatched CAP IDs

## Installation

1. Ensure you have Python 3.6 or higher installed

2. Install required package:

   ```bash
   pip install pandas
   ```

## Input Files

1. **Cadet_Orientation_Report.csv** (required for points calculation)
   - Download from CAP E-Services Orientation Flights Report
   - Contains cadet flight history and information

2. **cadet_list.txt** (required for slot assignment)
   - One CAP ID per line
   - Example:

     ```text
     123456
     234567
     345678
     ```

## Usage

### Complete Workflow (Points + Slots)

```bash
python oflight.py <number_of_slots>
```

Example:

```bash
python oflight.py 10
```

### Individual Commands

1. Calculate Points Only:

   ```bash
   python oflight.py points
   ```

2. Create Slot Assignments Only:

   ```bash
   python oflight.py slots [number_of_slots]
   ```

## Output Files

1. **oflight_points.csv**
   - Contains processed data with point calculations
   - Used as input for slot assignments

2. **slotting.txt**
   - Lists primary slots and alternates
   - Shows for each cadet:
     - CAP ID
     - Name
     - Total Points
     - Next O-Flight Number (1-5)
     - Last Flight Date

## Point System Details

- **Flight Points**:
  - FLIGHT_FACTOR (5) points per remaining powered flight
  - NO_FLIGHT_FACTOR (5) extra points for cadets with no flights

- **Date Points**:
  - DATE_FACTOR (1) point per month since last flight or join date

## Example Output

```text
Primary Slots:
======================================================================
  #  CAPID    Name                           Points  Next  Last Flight
  1  123456   John Smith                      43     2       Apr-23
  2  234567   Jane Doe                        40     2       Jul-23

Alternates:
======================================================================
  3  345678   James Johnson                   36     1
```

## Customization

You can adjust the point system by modifying these variables in `oflight.py`:

- `NO_FLIGHT_FACTOR`: Weight for cadets with no flights
- `FLIGHT_FACTOR`: Weight for remaining flights
- `DATE_FACTOR`: Weight for time since last flight
