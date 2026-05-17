import argparse
from model import CelloCut

def main(args):
    voxel_res = args.voxel_res
    T = args.lamda_fill
    INPUT_FILE = args.input
    OUT_FILE  = args.output
    decimate_ratio = args.decimate_ratio

    model = CelloCut(voxel_res, T)
    model.remesh(INPUT_FILE, OUT_FILE, decimate_ratio)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='CelloCut watertight remeshing')
    parser.add_argument('--lamda_fill', '--lambda_fill', dest='lamda_fill', type=int, default=20, help='Filling regularization weight')
    parser.add_argument('--input', type=str, default='assets/bad_doll.obj', help='Input mesh file path')
    parser.add_argument('--output', type=str, default='results/output.obj', help='Output mesh file path')
    parser.add_argument('--voxel_res', type=int, default=512, help='Voxel resolution')
    parser.add_argument('--decimate_ratio', type=float, default=0.95, help='Fraction of proxy mesh faces removed before tetrahedralization')
    args = parser.parse_args()
    main(args)
    print("Done")
