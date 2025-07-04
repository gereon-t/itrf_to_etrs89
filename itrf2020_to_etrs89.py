import argparse
from datetime import datetime
import os
import numpy as np
from pyproj import Transformer
import trajectopy as tpy


ITRF2020_to_ETRS89 = {
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
    parser = argparse.ArgumentParser(description="Convert ITRF2020 coordinates to ETRS89 coordinates.")
    parser.add_argument(
        "--finp",
        type=str,
        required=False,
        help="Input trajectopy file in ITRF2020 format.",
        default="m10_igg_dach.traj",
    )
    parser.add_argument("--epoch", type=float, required=False, help="Epoch for the conversion.", default=None)
    parser.add_argument(
        "--fout", type=str, required=False, help="Output trajectopy file in ETRS89 format.", default="output.traj"
    )
    parser.add_argument(
        "--gsb",
        type=str,
        required=False,
        help="Path to the GSB file for horizontal grid shift transformation for R16 to R25.",
        default="R16_to_R25.gsb",
    )
    parser.add_argument(
        "--target_epsg",
        type=int,
        required=False,
        help="Target EPSG code for the output trajectory.",
        default=25832,  # ETRS89 / ETRS-GRS80 (geographic)
    )
    parser.add_argument(
        "--realization",
        type=str,
        required=False,
        help="Realization of ETRS89 to use (R16 or R25).",
        default="R25",
    )
    args = parser.parse_args()
    input_file = args.finp
    output_file = args.fout
    epoch = args.epoch
    gsb_file = args.gsb
    target_epsg = args.target_epsg

    trajectory = tpy.Trajectory.from_file(input_file)

    if epoch is None:
        mean_time = np.mean(trajectory.tstamps)
        mean_datetime = datetime.fromtimestamp(mean_time)
        epoch = mean_datetime.year + (mean_datetime.month - 1) / 12 + (mean_datetime.day - 1) / 365.25
        print(f"Using mean epoch: {epoch:.4f} (year.month)")

    trajectory.pos.to_epsg(4978)  # ITRF2020 / WGS 84 (geocentric)

    t_x = ITRF2020_to_ETRS89["T1"] + ITRF2020_to_ETRS89["dotT1"] * (epoch - ITRF2020_to_ETRS89["t0"])
    t_y = ITRF2020_to_ETRS89["T2"] + ITRF2020_to_ETRS89["dotT2"] * (epoch - ITRF2020_to_ETRS89["t0"])
    t_z = ITRF2020_to_ETRS89["T3"] + ITRF2020_to_ETRS89["dotT3"] * (epoch - ITRF2020_to_ETRS89["t0"])
    r_x = ITRF2020_to_ETRS89["R1"] + ITRF2020_to_ETRS89["dotR1"] * (epoch - ITRF2020_to_ETRS89["t0"])
    r_y = ITRF2020_to_ETRS89["R2"] + ITRF2020_to_ETRS89["dotR2"] * (epoch - ITRF2020_to_ETRS89["t0"])
    r_z = ITRF2020_to_ETRS89["R3"] + ITRF2020_to_ETRS89["dotR3"] * (epoch - ITRF2020_to_ETRS89["t0"])
    d = ITRF2020_to_ETRS89["D"] + ITRF2020_to_ETRS89["dotD"] * (epoch - ITRF2020_to_ETRS89["t0"])

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

    trajectory.apply_transformation(transformation_matrix)
    trajectory.pos.epsg = 4936  # ETRS89 / ETRS-GRS80 (geographic)

    abs_gsb_path = os.path.abspath(gsb_file)
    pipeline_str = (
        f"+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad "
        f"+step +proj=hgridshift +grids={abs_gsb_path} "
        f"+step +proj=unitconvert +xy_in=rad +xy_out=deg"
    )

    transformer = Transformer.from_pipeline(pipeline_str)

    if args.realization == "R16":
        print("Transforming to R2016.")
        trajectory.pos.to_epsg(4258)
        trafo_y, trafo_x, trafo_z = transformer.transform(
            trajectory.pos.y, trajectory.pos.x, trajectory.pos.z, direction="inverse"
        )
        trajectory.pos.xyz = np.array([trafo_x, trafo_y, trafo_z]).T

    trajectory.pos.to_epsg(target_epsg)  # Convert to target EPSG code
    trajectory.to_file(output_file)


if __name__ == "__main__":
    main()
