import s3fs
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), "Data")

def download_bhav():
    s3_params = {
        "endpoint_url": "https://cbabd13f6c54798a9ec05df5b8070a6e.r2.cloudflarestorage.com",
        "key": "5c8ea9c516abfc78987bc98c70d2868a",
        "secret": "0cf64f9f0b64f6008cf5efe1529c6772daa7d7d0822f5db42a7c6a1e41b3cadf",
        "client_kwargs": {
            "region_name": "auto"
        },
    }
    
    fs = s3fs.S3FileSystem(**s3_params)
    in_path = 's3://desiquant/data/bhav'
    out_path = os.path.join(_DATA_DIR, "bhav_dump")
    
    print(f"Calculating size of {in_path}...")
    try:
        total_size = fs.du(in_path)
        print(f"Total size: {total_size / (1024**2):.2f} MB")
        
        if total_size > 0:
            print(f"Downloading to {out_path}...")
            os.makedirs(out_path, exist_ok=True)
            fs.get(in_path, out_path, recursive=True)
            print("Download completed successfully!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    download_bhav()
