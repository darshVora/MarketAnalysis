import s3fs
import os
import re

_DATA_DIR = os.path.join(os.path.dirname(__file__), "Data")

def sanitize_filename(filename):
    # Windows invalid characters: < > : " / \ | ? *
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def custom_download(fs, s3_path, local_base_path):
    try:
        if fs.isdir(s3_path):
            files = fs.find(s3_path)
            for f in files:
                # Calculate relative path from the original s3_path to keep directory structure
                rel_path = os.path.relpath(f, s3_path)
                # Split paths to sanitize only folder/file names, not the OS separators
                parts = rel_path.replace('\\', '/').split('/')
                sanitized_parts = [sanitize_filename(p) for p in parts]
                safe_rel_path = os.path.join(*sanitized_parts)
                
                local_file_path = os.path.join(local_base_path, safe_rel_path)
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                
                try:
                    fs.get(f, local_file_path)
                except Exception as ex:
                    print(f"    Failed to download {f}: {ex}")
        else:
            # It's a single file
            filename = os.path.basename(s3_path)
            safe_filename = sanitize_filename(filename)
            local_file_path = os.path.join(local_base_path, safe_filename)
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            fs.get(s3_path, local_file_path)
            
        print(f"Successfully downloaded {s3_path}")
    except Exception as e:
        print(f"Error processing {s3_path}: {e}")

def download_aux_data():
    s3_params = {
        "endpoint_url": "https://cbabd13f6c54798a9ec05df5b8070a6e.r2.cloudflarestorage.com",
        "key": "5c8ea9c516abfc78987bc98c70d2868a",
        "secret": "0cf64f9f0b64f6008cf5efe1529c6772daa7d7d0822f5db42a7c6a1e41b3cadf",
        "client_kwargs": {
            "region_name": "auto"
        },
    }
    
    fs = s3fs.S3FileSystem(**s3_params)
    out_path = os.path.join(_DATA_DIR, "desiquant_aux")
    os.makedirs(out_path, exist_ok=True)
    
    paths_to_download = [
        's3://desiquant/data/holidays.csv',
        's3://desiquant/data/indices',
        's3://desiquant/data/instruments',
        's3://desiquant/data/iv',
        's3://desiquant/data/meta.csv',
        's3://desiquant/data/news',
        's3://desiquant/data/results',
        's3://desiquant/data/strikes',
        's3://desiquant/data/symbols'
    ]
    
    print(f"Beginning batch download into {out_path}...")
    for path in paths_to_download:
        print(f"Downloading {path}...")
        # Create a matching subdirectory in desiquant_aux for folders like 'indices'
        base_folder_name = sanitize_filename(os.path.basename(path))
        if fs.isdir(path):
            local_target_dir = os.path.join(out_path, base_folder_name)
        else:
            local_target_dir = out_path
            
        custom_download(fs, path, local_target_dir)
            
    print("All requested auxiliary datasets have been downloaded.")

if __name__ == "__main__":
    download_aux_data()
