import argparse
import os
import numpy as np
from pyproj import Transformer
import trajectopy as tpy


def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description="Convert between ETRS89 R2025 and R2016 using a GSB file.")
    parser.add_argument(
        "--finp",
        type=str,
        required=True,
        help="Input trajectopy.",
    )
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
        default=4936,
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
    gsb_file = args.gsb
    target_epsg = args.target_epsg
    direction = args.direction.lower()

    trajectory = tpy.Trajectory.from_file(input_file)
    trajectory.pos.to_epsg(4258)

    traj_in_utm = trajectory.pos.to_epsg(25832, inplace=False)

    abs_gsb_path = os.path.abspath(gsb_file)
    pipeline_str = (
        f"+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad "
        f"+step +proj=hgridshift +grids={abs_gsb_path} "
        f"+step +proj=unitconvert +xy_in=rad +xy_out=deg"
    )
    transformer = Transformer.from_pipeline(pipeline_str)
    trafo_y, trafo_x, trafo_z = transformer.transform(
        trajectory.pos.y, trajectory.pos.x, trajectory.pos.z, direction=direction
    )
    trajectory.pos.xyz = np.array([trafo_x, trafo_y, trafo_z]).T

    trajectory.pos.to_epsg(target_epsg)
    trajectory.to_file(output_file)

    traj_out_utm = trajectory.pos.to_epsg(25832, inplace=False)

    print(f"Transformed coordinates:")
    print(np.round(trajectory.pos.xyz, 4))

    print(f"Differences in UTM coordinates (EPSG:25832) [mm]:")
    print(np.round(1000 * (traj_out_utm.xyz - traj_in_utm.xyz), 4))

    mean_diff = np.mean(1000 * (traj_out_utm.xyz - traj_in_utm.xyz), axis=0)
    print(
        f"Mean difference in UTM coordinates (EPSG:25832) [mm]: {np.round(mean_diff, 4)}, total: {np.linalg.norm(mean_diff):.4f} mm"
    )


if __name__ == "__main__":
    main()
