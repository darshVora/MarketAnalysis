import s3fs

def check_single_symbol():
    s3_params = {
        "endpoint_url": "https://cbabd13f6c54798a9ec05df5b8070a6e.r2.cloudflarestorage.com",
        "key": "5c8ea9c516abfc78987bc98c70d2868a",
        "secret": "0cf64f9f0b64f6008cf5efe1529c6772daa7d7d0822f5db42a7c6a1e41b3cadf",
        "client_kwargs": {
            "region_name": "auto"
        },
    }
    
    fs = s3fs.S3FileSystem(**s3_params)
    path = 's3://desiquant/data/candles/AARTIIND'
    
    print(f"Listing {path}...")
    try:
        items = fs.ls(path)
        print(f"Found {len(items)} items. First 5:")
        for item in items[:5]:
            print(f" - {item}")
            
        total_size = fs.du(path)
        print(f"\nSize of {path}: {total_size / (1024**2):.2f} MB")
        
    except Exception as e:
        print(f"Error accessing bucket: {e}")

if __name__ == "__main__":
    check_single_symbol()
