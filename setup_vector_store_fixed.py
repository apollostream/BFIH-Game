"""
setup_vector_store.py (FIXED)
Initialize OpenAI Files API for treatise and scenario templates

This script:
1. Uses OpenAI Files API (available in all versions)
2. Uploads the intellectual honesty treatise
3. Saves file IDs to .env
4. Works with openai >= 1.0.0
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, List

from openai import OpenAI
from dotenv import load_dotenv, set_key


load_dotenv()

TREATISE_VECTOR_STORE_ID = os.getenv("TREATISE_VECTOR_STORE_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY not found in .env")
    print("Please set your OpenAI API key first")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)


# ============================================================================
# FILES API OPERATIONS
# ============================================================================

def upload_file(file_path: str, vector_store_id: str = TREATISE_VECTOR_STORE_ID) -> Optional[str]:
    """Upload file to OpenAI Files API"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"⚠ File not found: {file_path}")
        return None
    
    print(f"\n📤 Uploading: {file_path.name}...")
    
    try:
        with open(file_path, 'rb') as f:
            response = client.files.create(
                file=f,
                purpose="assistants"
            )
        print(f"✓ Uploaded: {file_path.name}")
        print(f"  File ID: {response.id}")
        
        if vector_store_id:
            vector_store_file = client.vector_stores.files.create(
                vector_store_id=vector_store_id,
                file_id=response.id
            )
            print(f"  Vector Store File ID: {vector_store_file.id}")
            print(f"  Vector Store ID: {vector_store_id}")
        
        return vector_store_file.id
        
    except Exception as e:
        print(f"✗ Error uploading {file_path.name}: {str(e)}")
        return None


def list_files() -> List[dict]:
    """List all uploaded files"""
    print("\n📚 Your Uploaded Files:")
    
    try:
        files = client.files.list()
        
        if not files.data:
            print("  (none)")
            return []
        
        file_list = []
        for i, file in enumerate(files.data, 1):
            print(f"  {i}. {file.filename} (ID: {file.id}) - {file.size} bytes")
            file_list.append({
                "id": file.id,
                "name": file.filename,
                "size": file.size
            })
        
        return file_list
        
    except Exception as e:
        print(f"✗ Error listing files: {str(e)}")
        return []


def delete_file(file_id: str, vector_store_id: str = TREATISE_VECTOR_STORE_ID) -> bool:
    """Delete a file"""
    try:
        if vector_store_id:
            deleted_vector_store_file = client.vector_stores.files.delete(
              vector_store_id = vector_store_id,
              file_id=file_id
            )
        client.files.delete(file_id)
        print(f"✓ Deleted file: {file_id}")
        return True
    except Exception as e:
        print(f"✗ Error deleting file: {str(e)}")
        return False


def update_env_file(key: str, value: str):
    """Update .env file with new value"""
    env_path = Path(".env")
    
    if env_path.exists():
        set_key(".env", key, value)
        print(f"\n✓ Updated .env: {key}={value}")
    else:
        print(f"⚠ .env file not found")


# ============================================================================
# INTERACTIVE SETUP
# ============================================================================

def interactive_setup():
    """Interactive file setup"""
    
    print("\n" + "="*60)
    print("BFIH Backend: Files API Setup")
    print("="*60)
    
    print("\nUsing OpenAI Files API for document management")
    print("(Compatible with all openai >= 1.0.0 versions)")
    
    # Option menu
    print("\nOptions:")
    print("1. Upload treatise and scenario files")
    print("2. List uploaded files")
    print("3. Delete a file")
    print("4. Done")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "2":
        list_files()
        return
    
    if choice == "3":
        file_id = input("Enter file ID to delete: ").strip()
        if delete_file(file_id):
            print("✓ File deleted successfully")
        return
    
    if choice != "1":
        print("Invalid option")
        return
    
    # Upload files
    print("\n" + "="*60)
    print("Upload Files")
    print("="*60)
    
    files_to_upload = [
        ("Intellectual-Honesty_rev-4.pdf", "treatise"),
        ("TEMPLATE-final-report-of-full-analysis.md", "template"),
        ("ai-hypothesis-tournament-v2.md", "game_rules")
    ]
    
    uploaded_files = {}
    for file_name, file_type in files_to_upload:
        if Path(file_name).exists():
            file_id = upload_file(file_name)
            if file_id:
                uploaded_files[file_type] = {
                    "filename": file_name,
                    "file_id": file_id
                }
        else:
            print(f"⚠ Skipping {file_name} (not found in current directory)")
    
    if uploaded_files:
        print(f"\n✓ Successfully uploaded {len(uploaded_files)} file(s)")
        
        # Save to .env
        for file_type, info in uploaded_files.items():
            env_key = f"{file_type.upper()}_FILE_ID"
            update_env_file(env_key, info["file_id"])
        
        # Also save a JSON config for reference
        config = {
            "uploaded_files": uploaded_files,
            "setup_date": __import__("datetime").datetime.utcnow().isoformat(),
            "instructions": "Use these file IDs in your API calls with file_search"
        }
        
        with open("uploaded_files.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print("\n✓ File configuration saved to uploaded_files.json")
        
        print("\n" + "="*60)
        print("✓ Setup Complete!")
        print("="*60)
        print("\nYour files are now available via OpenAI Files API")
        print("\nFile IDs saved to .env:")
        for file_type, info in uploaded_files.items():
            print(f"  {file_type.upper()}_FILE_ID={info['file_id']}")
        
        print("\nHow to use in your API calls:")
        print("  1. Reference file IDs in your prompts")
        print("  2. Use file_search tool in Responses API")
        print("  3. Or use file IDs with Assistants API")
    else:
        print("\n✗ No files were uploaded")


# ============================================================================
# HELPER: Show minimal working example
# ============================================================================

def show_usage_example():
    """Show how to use uploaded files in API calls"""
    
    example = """
# Example: Using uploaded files with Responses API

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Get file IDs from environment
treatise_file_id = os.getenv("TREATISE_FILE_ID")

# Use in Responses API
response = client.responses.create(
    model="gpt-4o",
    input=f"Analyze this hypothesis: {{hypothesis}}",
    tools=[
        {{
            "type": "file_search",
            "file_ids": [treatise_file_id]
        }}
    ]
)

print(response.content[0].text)
"""
    
    return example


if __name__ == "__main__":
    
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(__doc__)
        print("\nUsage:")
        print("  python setup_vector_store.py          # Interactive setup")
        print("  python setup_vector_store.py --help   # Show this help")
        sys.exit(0)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--example":
        print("\nExample: Using Files in API Calls")
        print(show_usage_example())
        sys.exit(0)
    
    interactive_setup()
