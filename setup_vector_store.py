"""
setup_vector_store.py
Initialize OpenAI Vector Stores with treatise and scenario templates

This script:
1. Creates a new vector store
2. Uploads the intellectual honesty treatise
3. Uploads scenario templates
4. Saves the vector store ID to .env
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional

from openai import OpenAI
from dotenv import load_dotenv, set_key


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY not found in .env")
    print("Please set your OpenAI API key first")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)


def create_vector_store(name: str = "BFIH_Knowledge_Base") -> str:
    """Create new vector store"""
    print(f"\n📦 Creating vector store: {name}...")
    
    vs = client.beta.vector_stores.create(name=name)
    
    print(f"✓ Vector store created: {vs.id}")
    return vs.id


def upload_file_to_store(vector_store_id: str, file_path: str) -> Optional[str]:
    """Upload file to vector store"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"⚠ File not found: {file_path}")
        return None
    
    print(f"\n📤 Uploading: {file_path.name}...")
    
    try:
        with open(file_path, 'rb') as f:
            response = client.beta.vector_stores.files.create(
                vector_store_id=vector_store_id,
                file=f
            )
        
        print(f"✓ Uploaded: {file_path.name} (ID: {response.id})")
        return response.id
        
    except Exception as e:
        print(f"✗ Error uploading {file_path.name}: {str(e)}")
        return None


def list_vector_stores():
    """List all vector stores"""
    print("\n📚 Available Vector Stores:")
    
    stores = client.beta.vector_stores.list()
    
    if not stores.data:
        print("  (none)")
        return
    
    for i, store in enumerate(stores.data, 1):
        print(f"  {i}. {store.name} (ID: {store.id})")


def update_env_file(key: str, value: str):
    """Update .env file with new value"""
    env_path = Path(".env")
    
    if env_path.exists():
        set_key(".env", key, value)
        print(f"\n✓ Updated .env: {key}={value}")
    else:
        print(f"⚠ .env file not found")


def interactive_setup():
    """Interactive vector store setup"""
    
    print("\n" + "="*60)
    print("BFIH Backend: Vector Store Setup")
    print("="*60)
    
    # Option 1: Use existing vector store
    print("\nOptions:")
    print("1. Create new vector store and upload files")
    print("2. Use existing vector store")
    print("3. List available vector stores")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "3":
        list_vector_stores()
        return
    
    if choice == "2":
        vector_store_id = input("\nEnter vector store ID: ").strip()
        if vector_store_id.startswith("vs_"):
            update_env_file("TREATISE_VECTOR_STORE_ID", vector_store_id)
            print("✓ Vector store ID saved to .env")
        else:
            print("✗ Invalid vector store ID format (should start with 'vs_')")
        return
    
    if choice != "1":
        print("Invalid option")
        return
    
    # Create new vector store
    vector_store_id = create_vector_store()
    
    # Find and upload files
    files_to_upload = [
        "Intellectual-Honesty_rev-4.pdf",
        "TEMPLATE-final-report-of-full-analysis.md",
        "ai-hypothesis-tournament-v2.md"
    ]
    
    uploaded_count = 0
    for file_name in files_to_upload:
        if Path(file_name).exists():
            if upload_file_to_store(vector_store_id, file_name):
                uploaded_count += 1
        else:
            print(f"⚠ Skipping {file_name} (not found in current directory)")
    
    if uploaded_count > 0:
        print(f"\n✓ Successfully uploaded {uploaded_count} file(s)")
        
        # Save to .env
        update_env_file("TREATISE_VECTOR_STORE_ID", vector_store_id)
        
        print("\n" + "="*60)
        print("✓ Vector Store Setup Complete!")
        print("="*60)
        print(f"\nYour vector store ID: {vector_store_id}")
        print("This has been saved to .env as TREATISE_VECTOR_STORE_ID")
    else:
        print("\n✗ No files were uploaded")


def create_scenario_template() -> str:
    """Create a sample scenario JSON template"""
    
    template = {
        "scenario_id": "s_template_001",
        "title": "Sample Hypothesis Tournament Scenario",
        "domain": "business",
        "difficulty_level": "medium",
        "scenario_config": {
            "paradigms": [
                {
                    "id": "K1",
                    "name": "Secular-Individualist",
                    "description": "Success driven by individual effort and market forces"
                },
                {
                    "id": "K2",
                    "name": "Religious-Communitarian",
                    "description": "Success driven by faith and community networks"
                },
                {
                    "id": "K3",
                    "name": "Economistic-Rationalist",
                    "description": "Success driven by capital efficiency and data"
                }
            ],
            "hypotheses": [
                {
                    "id": "H0",
                    "name": "Unknown/Combination",
                    "domains": [],
                    "associated_paradigms": ["K1", "K2", "K3"],
                    "is_catch_all": True,
                    "description": "Success due to combination of factors"
                },
                {
                    "id": "H1",
                    "name": "Founder Vision & Execution",
                    "domains": ["Psychological", "Strategic"],
                    "associated_paradigms": ["K1"],
                    "description": "Strong founder vision and relentless execution"
                },
                {
                    "id": "H2",
                    "name": "Community Backing",
                    "domains": ["Theological", "Cultural", "Social"],
                    "associated_paradigms": ["K2"],
                    "description": "Strong backing from faith-based or tight-knit communities"
                },
                {
                    "id": "H3",
                    "name": "Capital Efficiency",
                    "domains": ["Economic"],
                    "associated_paradigms": ["K3"],
                    "description": "Exceptional capital efficiency and unit economics"
                }
            ],
            "priors_by_paradigm": {
                "K1": {"H0": 0.10, "H1": 0.60, "H2": 0.15, "H3": 0.15},
                "K2": {"H0": 0.10, "H1": 0.15, "H2": 0.60, "H3": 0.15},
                "K3": {"H0": 0.10, "H1": 0.15, "H2": 0.15, "H3": 0.60}
            }
        }
    }
    
    return template


if __name__ == "__main__":
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_setup()
    else:
        interactive_setup()
