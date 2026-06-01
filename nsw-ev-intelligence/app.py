# Read the working minimal version from the successful deployment
with open('/tmp/NSW-EV-Intelligence-Platform/nsw-ev-intelligence/app.py', 'r') as f:
    # This will be empty, so let's recreate from scratch
    pass

# Create the complete full-featured app from scratch
complete_app = open('/tmp/app_full_featured.py', 'r').read()

# Verify it's not empty
if len(complete_app) < 1000:
    print("ERROR: Source file is too small!")
else:
    # Save to an easy-to-find location in workspace
    workspace_path = '/Workspace/Users/moeedk1@gmail.com/DOWNLOAD_THIS_app.py'
    
    with open(workspace_path, 'w') as f:
        f.write(complete_app)
    
    print("✓ Complete app.py created successfully!")
    print(f"✓ File size: {len(complete_app):,} bytes")
    print(f"✓ Location: {workspace_path}")
    print("")
    print("=" * 70)
    print("INSTRUCTIONS:")
    print("=" * 70)
    print("1. In Databricks workspace, navigate to:")
    print("   /Users/moeedk1@gmail.com/DOWNLOAD_THIS_app.py")
    print("")
    print("2. Open the file")
    print("")
    print("3. Select ALL content (Ctrl+A / Cmd+A)")
    print("")
    print("4. Copy it (Ctrl+C / Cmd+C)")
    print("")
    print("5. Go to GitHub:")
    print("   https://github.com/abdulmoeedkhan123/NSW-EV-Intelligence-Platform")
    print("   /blob/main/nsw-ev-intelligence/app.py")
    print("")
    print("6. Click Edit (pencil icon)")
    print("")
    print("7. Select all existing content and DELETE it")
    print("")
    print("8. Paste the copied content")
    print("")
    print("9. Commit with message: 'Add full-featured EV Intelligence app'")
    print("=" * 70)
    
    # Show first and last few lines to verify
    lines = complete_app.split('\n')
    print("")
    print("Preview - First 10 lines:")
    print('\n'.join(lines[:10]))
    print("")
    print("Preview - Last 10 lines:")
    print('\n'.join(lines[-10:]))