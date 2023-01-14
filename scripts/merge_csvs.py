import enum
import glob
import pandas as pd
import csv

from typing import Any, List, NamedTuple, Tuple


df = None


class Code(enum.Enum):
    Success = 0
    Error = 1


EutraHeaders = [
    "ECellID",
    "CellName",
    "Longitude",
    "Latitude",
    "PCI",
    "EARFCN",
    "Azimuth",
]
ValidEutraHeader = ",".join(EutraHeaders)


def validateEutraCell(
    cellCsv: NamedTuple(
        "Cell",
        ECellID=Any,
        CellName=Any,
        Longitude=Any,
        Latitude=Any,
        PCI=Any,
        EARFCN=Any,
        Azimuth=Any,
    )
) -> Tuple[Code, str]:
    global df

    for col in EutraHeaders:
        if col not in cellCsv._fields:
            return Code.Error, f"Missing column `{col}`"

        match col:
            case "ECellID":
                # Max 24 bits
                max_val = 2 ** 28 - 1

                # Must be int
                if not isinstance(getattr(cellCsv, col), int):
                    return Code.Error, f"`{col}` must be an int"
                if getattr(cellCsv, col) > max_val:
                    return Code.Error, f"Invalid value for `{col}` (above max value)"
                if getattr(cellCsv, col) < 0:
                    return Code.Error, f"Invalid value for `{col}` (below min value - 0)"

            case "CellName":
                stringified  = str(getattr(cellCsv, col))

                if len(stringified) > 128:
                    return Code.Error, f"Invalid value for `{col}` (above max length of 128 chars)"

            case "Longitude":
                # Must be float
                if not isinstance(getattr(cellCsv, col), float):
                    return Code.Error, f"`{col}` must be a float"
                if getattr(cellCsv, col) < -180 or getattr(cellCsv, col) > 180:
                    return Code.Error, f"Invalid value for `{col}` (outside range: -180 to 180)"
                
            case "Latitude":
                # Must be float
                if not isinstance(getattr(cellCsv, col), float):
                    return Code.Error, f"`{col}` must be a float"
                if getattr(cellCsv, col) < -90 or getattr(cellCsv, col) > 90:
                    return Code.Error, f"Invalid value for `{col}` (outside range: -90 to 90)"
            
            case "PCI":
                # Must be int between 0 and 511
                if not isinstance(getattr(cellCsv, col), int):
                    return Code.Error, f"`{col}` must be an int"
                if getattr(cellCsv, col) < 0 or getattr(cellCsv, col) > 511:
                    return Code.Error, f"Invalid value for `{col}` (outside range: 0 to 511)"

            case "EARFCN":
                # Must be int between -1 and 70000
                if not isinstance(getattr(cellCsv, col), int):
                    print(df.index[type(df[col]) == 'float'].tolist())
                    return Code.Error, f"`{col}` must be an int"

                if getattr(cellCsv, col) < -1 or getattr(cellCsv, col) > 70000:
                    return Code.Error, f"Invalid value for `{col}` (outside range: 0 to 70000)"

            case "Azimuth":
                # Must be int between 0 and 360
                if not isinstance(getattr(cellCsv, col), int):
                    return Code.Error, f"`{col}` must be an int"
                if getattr(cellCsv, col) < -1 or getattr(cellCsv, col) > 360:
                    return Code.Error, f"Invalid value for `{col}` (outside range: 0 to 360)"

    return Code.Success, ""



def mergeRatCellLists(rat) -> Code:
    global df

    if not (rat in ["eutra", "wcdma", "tscdma", "cdma", "gsm"]):
        print(f"Invalid RAT: {rat}")
        return Code.Error

    # Get all cell files matching the rat
    cell_files = glob.glob(f"../fragments/**/cells_{rat}.csv", recursive=True)

    # Store cells in hash map for O(1) lookup -- keys are of format `cellid__arfcn`
    cells_hash_map = {}

    print(f"Found {len(cell_files)} cell files for {rat}")

    if (len(cell_files) == 0):
        print(f"No cell files found for {rat}")
        return Code.Error

    # Iterate over all cell files
    for cell_file in cell_files:
        print(f"Processing {cell_file}")

        # Open cell file
        df = pd.read_csv(cell_file)

        # Validate header
        header = ",".join(df.columns.values.tolist())

        if header != ValidEutraHeader:
            print(f"Invalid header in `{cell_file}`")
            print(f"Expected: {ValidEutraHeader}")
            print(f"Got     : {header}")
            return Code.Error

        # Cap CellName to 128 chars
        df['CellName'] = df['CellName'].str[:128]

        # Iterate over all rows
        # https://medium.com/@formigone/stop-using-df-iterrows-2fbc2931b60e
        for row in df.itertuples():
            # Include header, and start from 1, not 0
            row_num = row.Index + 2

            # Validate cell
            code, msg = validateEutraCell(row)

            if code == Code.Error:
                print(f"Invalid cell in `{cell_file}`, row number {row_num}")
                print(f"{msg}")
                print(f"Row: {list(row)[1:]}")

                return Code.Error

            cell_key = f"{row.ECellID}__{row.EARFCN}__{row.PCI}"

            if cell_key in cells_hash_map:
                print(f"Duplicate cell in `{cell_file}`, row number {row_num}")
                print(f"Key already exists: {cell_key}")
                print(f"Existing cell: ID = {cells_hash_map[cell_key]['ECellID']}, Name = {cells_hash_map[cell_key]['CellName']}")
                return Code.Error
            
            row_dict = row._asdict()
            del row_dict['Index']

            cells_hash_map[cell_key] = row_dict

    # Merge cells!
    print("--------------")
    print(f"Merging cells for {rat}")
    with open(f"../merged_cells_{rat}.csv", "w") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)

        writer.writerow(EutraHeaders)

        for cell in cells_hash_map.values():
            writer.writerow(cell.values())

    print(f"Successfully merged {len(cells_hash_map.keys())} cells for {rat}")

    return Code.Success

val = mergeRatCellLists("eutra")

print(f"\nReturn code {val}")

if (val == Code.Error):
    exit(1)
