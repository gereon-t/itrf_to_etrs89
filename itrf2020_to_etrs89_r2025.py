import argparse
from datetime import datetime
import numpy as np
import trajectopy as tpy


ITRF2020_to_ETRS89_R2025 = {
    "t0": 2015.0,
    "T1": 41.1393,
    "T2": 51.9830,
    "T3": -101.1455,
    "D": 7.8918,
    "R1": 0.8878,
    "R2": 12.7748,
    "R3": -22.2616,
    "dotT1": 0,
    "dotT2": 0,
    "dotT3": 0,
    "dotD": 0,
    "dotR1": 0.086,
    "dotR2": 0.519,
    "dotR3": -0.753,
}


def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description="Convert ITRF2020 coordinates to ETRS89 R2025 coordinates.")
    parser.add_argument(
        "--finp",
        type=str,
        required=True,
        help="Input trajectopy file.",
    )
    parser.add_argument("--epoch", type=float, required=False, help="Epoch for the conversion.", default=None)
    parser.add_argument(
        "--fout", type=str, required=False, help="Output trajectopy file in ETRS89 format.", default="output.traj"
    )
    parser.add_argument(
        "--target_epsg",
        type=int,
        required=False,
        help="Target EPSG code for the output trajectory.",
        default=4936,  # ETRS89 / ETRS-GRS80 (geographic)
    )
    parser.add_argument(
        "--direction",
        type=str,
        required=False,
        help="Direction of transformation (forward or inverse).",
        default="forward",
    )
    args = parser.parse_args()
    input_file = args.finp
    output_file = args.fout
    epoch = args.epoch
    target_epsg = args.target_epsg

    trajectory = tpy.Trajectory.from_file(input_file)

    if epoch is None:
        mean_time = np.mean(trajectory.tstamps)
        mean_datetime = datetime.fromtimestamp(mean_time)
        epoch = mean_datetime.year + (mean_datetime.month - 1) / 12 + (mean_datetime.day - 1) / 365.25
        print(f"Using mean epoch: {epoch:.4f} (year.month)")

    trajectory.pos.to_epsg(4978)  # ITRF2020 / WGS 84 (geocentric)

    t_x = ITRF2020_to_ETRS89_R2025["T1"] + ITRF2020_to_ETRS89_R2025["dotT1"] * (epoch - ITRF2020_to_ETRS89_R2025["t0"])
    t_y = ITRF2020_to_ETRS89_R2025["T2"] + ITRF2020_to_ETRS89_R2025["dotT2"] * (epoch - ITRF2020_to_ETRS89_R2025["t0"])
    t_z = ITRF2020_to_ETRS89_R2025["T3"] + ITRF2020_to_ETRS89_R2025["dotT3"] * (epoch - ITRF2020_to_ETRS89_R2025["t0"])
    r_x = ITRF2020_to_ETRS89_R2025["R1"] + ITRF2020_to_ETRS89_R2025["dotR1"] * (epoch - ITRF2020_to_ETRS89_R2025["t0"])
    r_y = ITRF2020_to_ETRS89_R2025["R2"] + ITRF2020_to_ETRS89_R2025["dotR2"] * (epoch - ITRF2020_to_ETRS89_R2025["t0"])
    r_z = ITRF2020_to_ETRS89_R2025["R3"] + ITRF2020_to_ETRS89_R2025["dotR3"] * (epoch - ITRF2020_to_ETRS89_R2025["t0"])
    d = ITRF2020_to_ETRS89_R2025["D"] + ITRF2020_to_ETRS89_R2025["dotD"] * (epoch - ITRF2020_to_ETRS89_R2025["t0"])

    t_x /= 1000
    t_y /= 1000
    t_z /= 1000

    r_x *= 1 / 1000 * 1 / 3600 * np.pi / 180
    r_y *= 1 / 1000 * 1 / 3600 * np.pi / 180
    r_z *= 1 / 1000 * 1 / 3600 * np.pi / 180

    d /= 1e9
    d += 1

    # Apply the transformation
    transformation_matrix = np.array([[d, -r_z, r_y, t_x], [r_z, d, -r_x, t_y], [-r_y, r_x, d, t_z], [0, 0, 0, 1]])

    if args.direction.lower() == "inverse":
        print("Applying inverse transformation (ITRF2020 to ETRS89).")
        transformation_matrix = np.linalg.inv(transformation_matrix)

    trajectory.apply_transformation(transformation_matrix)
    trajectory.pos.epsg = 4936
    trajectory.pos.to_epsg(target_epsg)
    trajectory.to_file(output_file)

    print(f"Transformed positions:")
    print(np.round(trajectory.pos.xyz, 4))


if __name__ == "__main__":
    main()
