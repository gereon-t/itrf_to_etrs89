# ITRF2020 to ETRS89

This script converts [Trajectopy](https://github.com/gereon-t/trajectopy) trajectory files from ITRF2020 to ETRS89. It uses the transformation parameters provided by the [Arbeitsgemeinschaft der Vermessungsverwaltungen (AdV)](https://www.adv-online.de/AdV-Produkte/Integrierter-geodaetischer-Raumbezug/Transformationsparameter/ITRF2020-IGb20-ETRS89-DREF91-R2025/).

## Installing dependencies

```bash
pip install -r requirements.txt
```

## Usage

```bash
usage: itrf2020_to_etrs89.py [-h] --finp FINP [--epoch EPOCH] [--fout FOUT]

Convert ITRF2020 coordinates to ETRS89 coordinates.

options:
  -h, --help     show this help message and exit
  --finp FINP    Input trajectopy file in ITRF2020 format.
  --epoch EPOCH  Epoch for the conversion.
  --fout FOUT    Output trajectopy file in ETRS89 format.
```

If no epoch is provided, the epoch is extracted from the mean timestamp of the trajectory.

### Example using test.traj

```bash
python .\itrf2020_to_etrs89.py --finp .\test.traj --epoch 2021.48  --fout test_trafo.traj
```