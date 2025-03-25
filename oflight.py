"""
CAP Cadet Orientation Flight Points and Slotting Tool

This script combines two functions:
1. Processing orientation flight data to calculate priority points
2. Creating prioritized flight slot assignments

Usage:
1. Complete workflow (points + slots):
   python oflight.py <number_of_slots>
   Example: python oflight.py 10

2. Individual commands:
   Calculate points only:  python oflight.py points
   Assign slots only:     python oflight.py slots [number_of_slots]

Requirements:
- Python 3.6 or higher
- pandas library (install install pandas)

Point System:
- Flight Points: Points based on remaining powered flights
  * FLIGHT_FACTOR (default=5) points per remaining flight
  * NO_FLIGHT_FACTOR (default=5) extra points for no flights
- Date Points: Points based on months since last flight
  * DATE_FACTOR (default=1) point per month since last flight

Input Files:
- Points calculation: Cadet_Orientation_Report.csv (from E-Services)
- Slot assignments: cadet_list.txt (one CAP ID per line)

Output Files:
- Points calculation: oflight_points.csv
- Slot assignments: slotting.txt
"""

import pandas as pd
from datetime import datetime
import logging
import sys
from typing import Optional, Dict, Any, List
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Global configuration
NO_FLIGHT_FACTOR = 5      # Extra Points for cadets with no powered flights
FLIGHT_FACTOR = 5         # Points per powered flight
DATE_FACTOR = 1          # Points per month since last powered flight

# Required columns in input CSV
REQUIRED_COLUMNS = {'Miles', 'Textbox39', 'Textbox25', 'GroupType', 'Joined'}

def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parses a date string into a datetime object.
    """
    try:
        # Handle dates in MMM-YY format (e.g., "Mar-25")
        if len(date_str.split('-')) == 2:
            return datetime.strptime(date_str + "-01", "%b-%y-%d")
        # Handle dates in DD MMM YYYY format (e.g., "09 Mar 2023")
        return datetime.strptime(date_str, "%d %b %Y")
    except Exception as e:
        logging.error(f"Error parsing date {date_str}: {str(e)}")
        return None

def calculate_months_since(date_str: str) -> int:
    """
    Calculates the number of months since a given date.
    """
    if not date_str:
        return 0
    
    parsed_date = parse_date(date_str)
    if not parsed_date:
        return 0
    
    today = datetime.now()
    months = (today.year - parsed_date.year) * 12 + (today.month - parsed_date.month)
    return max(0, months)  # Ensure we don't return negative months

def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renames columns in the DataFrame to more readable names.

    Args:
        df (pd.DataFrame): The DataFrame with original column names.

    Returns:
        pd.DataFrame: The DataFrame with renamed columns.
    """
    column_mapping: Dict[str, str] = {
        'Miles': '18+',
        'Textbox39': 'Wing',
        'Textbox25': 'Unit',
        'Textbox130': 'glider_1',
        'Textbox131': 'glider_2',
        'Textbox132': 'glider_3',
        'Textbox133': 'glider_4',
        'Textbox134': 'glider_5',
        'Textbox135': 'powered_1',
        'Textbox136': 'powered_2',
        'Textbox137': 'powered_3',
        'Textbox138': 'powered_4',
        'Textbox139': 'powered_5'
    }
    return df.rename(columns=column_mapping)

def find_last_powered_date(row: pd.Series) -> str:
    """
    Finds the last powered flight date in a row.

    Args:
        row (pd.Series): A row from a DataFrame containing flight data.

    Returns:
        str: The last powered flight date recorded.
    """
    for i in range(5, 0, -1):
        col = f'powered_{i}'
        if pd.notna(row[col]) and row[col].strip():
            return row[col]
    return row['Joined']

def count_powered_flights(row: pd.Series) -> int:
    """
    Counts the number of powered flights in a row.

    Args:
        row (pd.Series): A row from a DataFrame containing flight data.

    Returns:
        int: The number of powered flights recorded.
    """
    count = 0
    for i in range(1, 6):
        col = f'powered_{i}'
        if pd.notna(row[col]) and row[col].strip():
            count += 1
    return count

def calculate_flight_points(row: pd.Series) -> int:
    """
    Calculates the flight points for a row.

    Args:
        row (pd.Series): A row from a DataFrame containing flight data.

    Returns:
        int: The flight points calculated based on the number of powered flights.
    """
    if row['GroupType'] == 'No O-Flights':
        return (5 - row['powered_count']) * FLIGHT_FACTOR + NO_FLIGHT_FACTOR
    return (5 - row['powered_count']) * FLIGHT_FACTOR

def calculate_date_points(last_powered: str) -> int:
    """
    Calculates the date points for a row.

    Args:
        last_powered (str): The last powered flight date.

    Returns:
        int: The date points calculated based on the number of months since the last flight.
    """
    months = calculate_months_since(last_powered)
    return months * DATE_FACTOR

def calculate_total_points(row: pd.Series) -> int:
    """
    Calculates the total points for a row.

    Args:
        row (pd.Series): A row from a DataFrame containing flight data.

    Returns:
        int: The total points calculated by adding flight points and date points.
    """
    return row['flight_points'] + row['date_points']

def validate_dataframe(df: pd.DataFrame) -> None:
    """
    Validates that the DataFrame has all required columns.
    """
    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes the data to calculate points and sort cadets.
    """
    # Validate input data
    validate_dataframe(df)
    
    # Rename columns for clarity
    df = rename_columns(df)
    
    # Calculate powered flight count for each cadet
    df['powered_count'] = df.apply(count_powered_flights, axis=1)
    
    # Find last powered flight date
    df['last_powered'] = df.apply(find_last_powered_date, axis=1)
    
    # Calculate points
    df['flight_points'] = df.apply(calculate_flight_points, axis=1)
    df['date_points'] = df['last_powered'].apply(calculate_date_points)
    df['total_points'] = df.apply(calculate_total_points, axis=1)
    
    # Sort by total points (descending)
    return df.sort_values('total_points', ascending=False)

def read_cadet_list(filename: str) -> List[str]:
    """
    Read a list of CAP IDs from a file, removing duplicates while preserving order.

    Args:
        filename (str): The path to the file containing the cadet list.

    Returns:
        List[str]: A list of unique CAP IDs.
    """
    try:
        with open(filename, 'r') as f:
            cap_ids = []
            seen = set()
            for line in f:
                cap_id = line.strip()
                if cap_id and cap_id not in seen:
                    cap_ids.append(cap_id)
                    seen.add(cap_id)
        return cap_ids
    except Exception as e:
        print(f"Error reading cadet list: {e}")
        return []

def format_last_flight(row: pd.Series) -> str:
    """
        Formats the last powered flight date in a row to the MMM-YY format.

    Args:
        row (pd.Series): A row from a DataFrame containing flight data.

    Returns:
        str: The last powered flight date in MMM-YY format, or an empty string if no powered flights.
    """
    if row['powered_count'] == 0:
        return ""
    
    for i in range(5, 0, -1):
        col = f'powered_{i}'
        if pd.notna(row[col]) and row[col].strip():
            try:
                date = datetime.strptime(row[col], "%b-%y")
                return date.strftime("%b-%y")
            except:
                return row[col]
    return ""

def write_slotting_results(filename: str, sorted_df: pd.DataFrame, unmatched_ids: List[str], slot_count: Optional[int] = None) -> None:
    """
    Writes the slotting results to a file.

    Args:
        filename (str): The path to the file where the results will be written.
        sorted_df (pd.DataFrame): The sorted DataFrame containing cadet data.
        unmatched_ids (List[str]): List of CAP IDs that did not match.
        slot_count (Optional[int]): Number of primary slots to write.
    """
    try:
        with open(filename, 'w') as f:
            header = f"{'#':>3}  {'CAPID':<8} {'Name':<30} {'Points':>3}  {'Next':>4}  {'Last Flight':<8}\n"
            if slot_count and len(sorted_df) > slot_count:
                # Write primary slots
                f.write("Primary Slots:\n")
                f.write("=" * 70 + "\n")
                f.write(header)
                primary_df = sorted_df.head(slot_count)
                for i, (_, row) in enumerate(primary_df.iterrows(), 1):
                    next_flight = row['powered_count'] + 1
                    last_flight = format_last_flight(row)
                    f.write(f"{i:>3}  {row['CAPID']:<8} {row['FullName']:<30} {row['total_points']:>3}     {next_flight:>1}       {last_flight:<8}\n")
                
                # Write alternates
                f.write("\nAlternates:\n")
                f.write("=" * 70 + "\n")
                f.write(header)
                alternates_df = sorted_df.iloc[slot_count:]
                for i, (_, row) in enumerate(alternates_df.iterrows(), slot_count + 1):
                    next_flight = row['powered_count'] + 1
                    last_flight = format_last_flight(row)
                    f.write(f"{i:>3}  {row['CAPID']:<8} {row['FullName']:<30} {row['total_points']:>3}     {next_flight:>1}       {last_flight:<8}\n")
            else:
                # Write all cadets in one list
                f.write("Cadets sorted by total points:\n")
                f.write("=" * 70 + "\n")
                f.write(header)
                for i, (_, row) in enumerate(sorted_df.iterrows(), 1):
                    next_flight = row['powered_count'] + 1
                    last_flight = format_last_flight(row)
                    f.write(f"{i:>3}  {row['CAPID']:<8} {row['FullName']:<30} {row['total_points']:>3}     {next_flight:>1}       {last_flight:<8}\n")
            
            if unmatched_ids:
                f.write("\nUnmatched CAP IDs:\n")
                f.write("=" * 20 + "\n")
                for cap_id in unmatched_ids:
                    f.write(f"{cap_id}\n")
        
        # Also print to console
        with open(filename, 'r') as f:
            print(f.read())
            
    except Exception as e:
        print(f"Error writing results: {e}")

def points_command():
    """
    Handle the points calculation command.

    This function reads the orientation report, processes the data to calculate points,
    and saves the results to a CSV file.
    """
    try:
        # Read and process the orientation report
        df = pd.read_csv("Cadet_Orientation_Report.csv")
        processed_df = process_data(df)
        
        # Save to CSV
        processed_df.to_csv("oflight_points.csv", index=False)
        logging.info("Points calculation complete. Results saved to oflight_points.csv")
        
    except Exception as e:
        logging.error(f"Error processing orientation report: {e}")
        sys.exit(1)

def slots_command(slot_count: Optional[int] = None):
    """
    Handle the slot assignment command.

    This function reads the cadet list and points CSV, filters the data,
    and writes the results to a file.
    """
    try:
        # Read the list of CAP IDs
        cap_ids = read_cadet_list("cadet_list.txt")
        
        # Read the points CSV
        df = pd.read_csv("oflight_points.csv")
        
        # Convert CAPID to string for matching
        df['CAPID'] = df['CAPID'].astype(str)
        
        # Filter for only the cadets in our list
        filtered_df = df[df['CAPID'].isin(cap_ids)]
        
        # Sort by total_points descending
        sorted_df = filtered_df.sort_values('total_points', ascending=False)
        
        # Find unmatched CAP IDs
        matched_ids = set(filtered_df['CAPID'])
        unmatched_ids = [id for id in cap_ids if id not in matched_ids]
        
        # Write results to file
        write_slotting_results("slotting.txt", sorted_df, unmatched_ids, slot_count)
        logging.info("Slot assignments complete. Results saved to slotting.txt")
            
    except Exception as e:
        logging.error(f"Error processing slot assignments: {e}")
        sys.exit(1)

def main():
    """
    Main function to handle command line interface.

    This function processes command line arguments and calls the appropriate command handler.
    """
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Complete workflow:   python oflight.py <number_of_slots>")
        print("  Calculate points:    python oflight.py points")
        print("  Assign slots:        python oflight.py slots [number_of_slots]")
        sys.exit(1)
        
    first_arg = sys.argv[1].lower()
    
    # Check if first argument is a number (complete workflow)
    try:
        slot_count = int(first_arg)
        # Run complete workflow
        logging.info("Starting complete workflow...")
        points_command()
        slots_command(slot_count)
        return
    except ValueError:
        # Not a number, process as command
        pass
        
    # Process individual commands
    if first_arg == "points":
        points_command()
    elif first_arg == "slots":
        slot_count = None
        if len(sys.argv) > 2:
            try:
                slot_count = int(sys.argv[2])
            except ValueError:
                print("Invalid slot count provided. Using no slot limit.")
        slots_command(slot_count)
    else:
        print(f"Unknown command or invalid slot count: {first_arg}")
        print("Usage:")
        print("  Complete workflow:   python oflight.py <number_of_slots>")
        print("  Calculate points:    python oflight.py points")
        print("  Assign slots:        python oflight.py slots [number_of_slots]")
        sys.exit(1)

if __name__ == "__main__":
    main()
