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
        return f'{self.ecellid},"{self.cellname}",{self.longitude},{self.latitude},{self.pci},{self.earfcn},{self.azimuth}'


def sendRequestWithCaptchaCheck(
    url, method="GET", params=None, headers=None, data=None
):
    status = "START"

    while status in ["START", "NEED_RECAPTCHA"]:
        if status == "NEED_RECAPTCHA":
            input(
                "Go to https://cellmapper.net and complete the ReCaptcha, then hit ENTER..."
            )

        data = request(method, url, params=params, headers=headers, data=data).json()

        status = data["statusCode"]

    if "responseData" not in data:
        print("Failed to fetch URI:", url)
        return None

    return data["responseData"]


def findTowersInBoundingBox(
    mcc: int, mnc: int, latNE: float, lonNE: float, latSW: float, lonSW: float
):
    # https://api.cellmapper.net/v6/getTowers
    # ?MCC=234&MNC=30
    # &RAT=LTE
    # &boundsNELatitude=51.17653502456466
    # &boundsNELongitude=-0.13659255219250147
    # &boundsSWLatitude=51.06011056714888
    # &boundsSWLongitude=-0.24746108529925182
    # &filterFrequency=false&showOnlyMine=false&showUnverifiedOnly=false&showENDCOnly=false

    query = {
        "MCC": mcc,
        "MNC": mnc,
        "RAT": "LTE",
        "boundsNELatitude": latNE,
        "boundsNELongitude": lonNE,
        "boundsSWLatitude": latSW,
        "boundsSWLongitude": lonSW,
        "filterFrequency": False,
        "showOnlyMine": False,
        "showUnverifiedOnly": False,
        "showENDCOnly": False,
    }

    data = sendRequestWithCaptchaCheck(f"{CELLMAPPER_API_ROOT}/getTowers", params=query)

    for tower in data:
        loadTowerData(mcc, mnc, tower["regionID"], tower["siteID"])


def loadTowerData(mcc: int, mnc: int, tac: int, site_id: int):
    query = {"MCC": mcc, "MNC": mnc, "Region": tac, "Site": site_id, "RAT": "LTE"}

    towerData = sendRequestWithCaptchaCheck(
        f"{CELLMAPPER_API_ROOT}/getTowerInformation", params=query
    )

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

    siteName = ", ".join(finalAddressParts)

    arfcns = towerData["channels"]

    cells: dict = towerData["cells"]

    cellIds = list(cells.keys())

    for i, cellId in enumerate(cellIds):
        if "PCI" not in cells[cellId]:
            print(f"Missing PCI for {mcc}-{mnc} {site_id} cell {cellId}")
            continue

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

# while True:
#     tac = input("Enter TAC (blank to export all cells to CSV): ")

#     if tac == "":
#         break

#     site_id = input("Enter Site ID (eNB): ")

#     if site_id == "":
#         continue

#     loadTowerData(mcc, mnc, tac, site_id)

latNE = input("Enter NE lat: ")
lonNE = input("Enter NE lon: ")
latSW = input("Enter SW lat: ")
lonSW = input("Enter SW lon: ")

findTowersInBoundingBox(mcc, mnc, latNE, lonNE, latSW, lonSW)

print("Exporting cells to CSV...")

with open("api.csv", "w") as f:
    for cell in CELLS:
        f.write(cell.toCsvString() + "\n")
