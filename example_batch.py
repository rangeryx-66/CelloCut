import argparse
import os
from model import CelloCut

def main(args):
    voxel_res = args.voxel_res
    T = args.lamda_fill
    INPUT_DIR = args.input_dir
    OUT_DIR = args.output_dir
    decimate_ratio = args.decimate_ratio

    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
        print(f"Created output directory: {OUT_DIR}")

    print(f"Initializing CelloCut with voxel_res={voxel_res}, lamda_fill={T}...")
    model = CelloCut(voxel_res, T)

    files = sorted(f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".obj"))
    
    total_files = len(files)
    print(f"Found {total_files} .obj files in {INPUT_DIR}")

    for idx, filename in enumerate(files):
        input_path = os.path.join(INPUT_DIR, filename)
        output_path = os.path.join(OUT_DIR, filename)

        print(f"[{idx+1}/{total_files}] Processing: {filename} ...")
        
        try:
            model.remesh(input_path, output_path, decimate_ratio)
        except Exception as e:
            print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Batch CelloCut watertight remeshing')
    
    parser.add_argument('--input_dir', type=str, default='dataset/benchmark', help='Input directory path')
    parser.add_argument('--output_dir', type=str, default='dataset/ours', help='Output directory path')
    parser.add_argument('--voxel_res', type=int, default=512, help='Voxel resolution')
    parser.add_argument('--decimate_ratio', type=float, default=0.95, help='Fraction of proxy mesh faces removed before tetrahedralization')
    parser.add_argument('--lamda_fill', '--lambda_fill', dest='lamda_fill', type=int, default=20, help='Filling regularization weight')
    
    args = parser.parse_args()
    main(args)
    print("All tasks done.")
