import json
from requests import request

CELLMAPPER_API_ROOT = "https://api.cellmapper.net/v6"
CELLS = []

CELLMAPPER_COOKIE_STR = None

try:
    with open("./cm_cookie") as f:
        CELLMAPPER_COOKIE_STR = f.read()
except FileNotFoundError:
    CELLMAPPER_COOKIE_STR = None

# Helps to bypass Captcha checks
SPOOF_HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "User-Agent": " Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
    "Origin": "https://www.cellmapper.net",
}

if CELLMAPPER_COOKIE_STR != None:
    print("Using CellMapper cookie from file")
    SPOOF_HEADERS["Cookie"] = CELLMAPPER_COOKIE_STR


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

    if "responseData" not in data:
        print("Failed to load tower data")
        return

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
    # if "neighbourhood" in siteAddress:
    #     addressParts.append(siteAddress["neighbourhood"])
    # if "village" in siteAddress:
    #     addressParts.append(siteAddress["village"])
    if "suburb" in siteAddress:
        addressParts.append(siteAddress["suburb"])
    if "town" in siteAddress:
        addressParts.append(siteAddress["town"])

    postcode = siteAddress["postcode"] if "postcode" in siteAddress else None

    if (postcode is not None) and (postcode != ""):
        finalAddressParts = addressParts[:3]
        finalAddressParts.append(postcode)
    else:
        finalAddressParts = addressParts[:4]

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
