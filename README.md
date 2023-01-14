# NSG Cell Database

Network Signal Guru is an application used to hook into low-level information and features of Android modems, including signalling data, cell lists, band locking and more.

NSG offers a feature called cell databases, which allows it to label cells on the cells list page when field testing with human-readable information, such as names, azimuths and more. This is useful so that you don't need to remember PCIs, cell IDs and node IDs of sites in your area.

> 🤑 Cell database importing is only allowed with NSG Premium. Importing a cell database with the free/trial version will have no effect.

## This project

The aim of this repository is to be an up-to-date source of cells across the globe(?) which anyone can contribute to, in order to better use Network Signal Guru.

## Automatic checks

Continuous integration (CI) is provided through GitHub Actions and does a few useful things:

- compiles every sublist within `fragments` into a master list
- ensures every sublist is valid and complies with the NSG cell list specification
- ensures no duplicates are found
  - since the cell list does not account for PLMNs, there is a **very small** chance that two Cell IDs + ARFCNs + PCIs can conflict
  - when a conflict occurs, it is likely required to remove such conflicting cells, usually in the suggested change rather than in the established dataset

## Contributing

The only way this project can grow is with **you**!

Mapping your local areas within this repository is the best way for it to grow and stay accurate.

### How to contribute

You'll need to start by making a 'fork' of this GitHub repository. This should be a button in the top-right of the screen at the top of this page. This makes a copy of the whole dataset on your own GitHub account.

From this fork, you can make changes to files within the dataset, including creating new files, deleting files and adding to files. Do so as needed, either with GitHub's web-based editor or by cloning the repository to your computer locally.

You can then open a Pull Request back to this repository with your changes.

**It is highly recommended that each Pull Request only edits one specific area/town/city. This helps with verifying information and processing reviews.**

> ℹ️ For more info, use Google, and check out GitHub's documentation: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork

### Repository structure

> ⚠️ **The full cell list is generated automatically and should not be edited directly. Changes made directly to this file will not be accepted.**

The cell list is generated from individual files within the `fragments` folder.

The general path structure is: `fragments/<2-letter country code>/<PLMN>/<region>/<town/city>/cells_<rat>.csv`, where `<rat>` is either `eutra`, `wcdma`, `tdscdma`, `cdma` or `gsm`.

Only files ending in `.csv` are automatically compiled into the complete list. This means that youcan create additional documentation files within any subdirectory of `fragments/` to detail naming schemes and other important info. Consensus should be that these files are named `README.md` and are found as high up within the folder structure as possible.

This structure is not strictly enforced, however. Large towns and cities could also be split into further subdirectories, such as London being split into individual London boroughs. If you're in doubt as to whether something should be in its own folder, _it probably should_.

### CSV requirements

The structure for CSV files can be found within the NSG user manual, but it is also included below for ease of use.

CSV files should be:

- saved in UTF-8 format
- contain all headers in the order provided below
- values should conform to the restrictions provided below

All aspects of files are automatically checked by automated tools, and issues will be reported automatically. Submissions with issues will not be accepted.

#### Structure

The structure of the CSV file varies between radio access technologies.

Initially, this repository will focus on LTE cells, but contributions for other radio access technologies is more than welcome.

##### LTE

File header: `ECellID,CellName,Longitude,Latitude,PCI,EARFCN,Azimuth`

| Field name | Description                                                          | Type                       | Example                                           |
| :--------: | -------------------------------------------------------------------- | -------------------------- | ------------------------------------------------- |
|  ECellID   | The identifying value for the LTE cell (**not** eNB ID) in the PLMN. | 28-bit integer             | `128121198`                                       |
|  CellName  | Name shown for the cell in the cell list. Location, then info.       | String, max 128 chars      | `Marchants Way, Burgess Hill - O2 Orion monopole` |
| Longitude  | Longitude of the site.                                               | Float                      | `0.13727388291219622`                             |
|  Latitude  | Latitude of the site.                                                | Float                      | `50.96678663980859`                               |
|   EARFCN   | EARFCN of the cell.                                                  | Integer (0 - 70000)        | `6400`                                            |
|    PCI     | LTE physical channel identity                                        | Integer (0 - 511)          | `172`                                             |
|  Azimuth   | Bearing of the centre of the cell.                                   | Integer (0 to 359 degrees) | Often `0`, `120` or `240`                         |
