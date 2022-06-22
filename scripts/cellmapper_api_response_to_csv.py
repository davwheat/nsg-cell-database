import json
from requests import request

CELLMAPPER_API_ROOT = "https://api.cellmapper.net/v6"
CELLS = []


class CSVCell:
    def __init__(self, ecellid, cellname, longitude, latitude, pci, earfcn, azimuth):
        self.ecellid = ecellid
        self.cellname = cellname
        self.longitude = longitude
        self.latitude = latitude
        self.pci = pci
        self.earfcn = earfcn
        self.azimuth = azimuth

    def toCsvString(self):
        return f"{self.ecellid},{self.cellname},{self.longitude},{self.latitude},{self.pci},{self.earfcn},{self.azimuth}"


def loadTowerData(mcc: int, mnc: int, tac: int, site_id: int):
    query = {"MCC": mcc, "MNC": mnc, "Region": tac, "Site": site_id, "RAT": "LTE"}

    status = "START"

    while status in ["START", "NEED_RECAPTCHA"]:
        if status == "NEED_RECAPTCHA":
            input(
                "Go to https://cellmapper.net and complete the ReCaptcha, then hit ENTER..."
            )

        data = request(
            "GET", f"{CELLMAPPER_API_ROOT}/getTowerInformation", params=query
        ).json()

        status = data["statusCode"]

    towerData = data["responseData"]

    # If towerData is string
    if isinstance(towerData, str):
        print("Failed to load tower data")
        return

    lat = towerData["latitude"]
    lon = towerData["longitude"]

    locationQuery = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "limit": 1,
        "callback": "?",
    }
    siteAddress = request(
        "GET", "https://nominatim.openstreetmap.org/reverse", params=locationQuery
    ).json()["address"]

    addressParts = []
    finalAddressParts = []

    if "road" in siteAddress:
        addressParts.append(siteAddress["road"])
    if "neighbourhood" in siteAddress:
        addressParts.append(siteAddress["neighbourhood"])
    if "town" in siteAddress:
        addressParts.append(siteAddress["town"])
    if "city" in siteAddress:
        addressParts.append(siteAddress["city"])

    postcode = siteAddress["postcode"] if "postcode" in siteAddress else None

    if (postcode is not None) and (postcode != ""):
        finalAddressParts = addressParts[:2]
        finalAddressParts.append(postcode)
    else:
        finalAddressParts = addressParts[:3]

    siteName = " | ".join(finalAddressParts)

    arfcns = towerData["channels"]

    cells: dict = towerData["cells"]

    cellIds = list(cells.keys())

    for i, cellId in enumerate(cellIds):
        cell = CSVCell(
            cellId,
            siteName,
            lon,
            lat,
            cells[cellId]["PCI"],
            arfcns[i],
            cells[cellId]["Bearing"],
        )

        CELLS.append(cell)


mcc = input("Enter MCC: ")
mnc = input("Enter MNC: ")

while True:
    tac = input("Enter TAC (blank to export all cells to CSV): ")

    if tac == "":
        break

    site_id = input("Enter Site ID (eNB): ")

    loadTowerData(mcc, mnc, tac, site_id)

print("Exporting cells to CSV...")

with open("api.csv", "w") as f:
    for cell in CELLS:
        f.write(cell.toCsvString() + "\n")
