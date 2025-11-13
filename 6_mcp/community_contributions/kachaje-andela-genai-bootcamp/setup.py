import os
import shutil


def init():
    """
    Check if required files exist locally. If not, check parent directory
    two levels up and copy them if found.
    """
    required_files = [
        'accounts.py',
        'accounts_client.py',
        'accounts_server.py',
        'database.py',
        'market.py',
        'market_server.py',
        'push_server.py'
    ]
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
    
    for filename in required_files:
        local_path = os.path.join(current_dir, filename)
        parent_path = os.path.join(parent_dir, filename)
        
        if os.path.exists(local_path):
            print(f"✓ {filename} already exists locally")
            continue
        
        if os.path.exists(parent_path):
            try:
                shutil.copy2(parent_path, local_path)
                print(f"✓ Copied {filename} from parent directory")
            except Exception as e:
                print(f"✗ Error copying {filename}: {e}")
        else:
            print(f"✗ Warning: {filename} not found locally or in parent directory")