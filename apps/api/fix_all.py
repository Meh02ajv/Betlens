import os

files = [
    'app/modules/assistant/router.py',
    'app/modules/notifications/router.py',
    'app/modules/billing/router.py',
    'app/modules/admin/router.py',
    'app/modules/sports_data/router.py',
    'app/modules/predictions/router.py',
    'app/modules/users/router.py',
    'app/modules/odds_value/router.py',
]

for filepath in files:
    if not os.path.exists(filepath):
        continue
    content = open(filepath).read()
    changed = False
    
    import re
    def fix_204(m):
        return m.group(0).replace('status_code=204', 'status_code=200')
    
    new_content = re.sub(r'@router\.(delete|post|put|patch)\([^)]*status_code=204[^)]*\)', fix_204, content)
    
    if new_content != content:
        # Also fix return types None -> dict
        new_content = new_content.replace(') -> None:\n', ') -> dict:\n')
        # Add return statement where missing after await db operations
        open(filepath, 'w').write(new_content)
        print(f'Fixed: {filepath}')
    else:
        print(f'No change: {filepath}')

print('All done!')