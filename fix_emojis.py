# -*- coding: utf-8 -*-
"""Fix Unicode emoji encoding in Python files"""
import os
import glob

# Emoji replacements
replacements = {
    '✅': '[OK]',
    '⚠️': '[WARNING]',
    '❌': '[ERROR]',
    '🔍': '[INFO]',
    '🛠️': '[TOOL]',
    '🏥': '[CLINIC]',
    '⚡': '[FAST]',
    '📊': '[STATS]',
    '🚀': '[START]',
    '💊': '[MED]',
    '⏰': '[CLOCK]',
    '🔄': '[CYCLE]',
    '💡': '[TIP]',
    '📍': '[LOCATION]',
    '🚗': '[TRAVEL]',
    '⚕️': '[MEDICAL]',
    '🧠': '[BRAIN]',
    '📱': '[PHONE]',
}

tools_dir = r'c:\Users\Tanay Mehta\OneDrive\Desktop\Tanay IMP\Hackathons\Mumbai_Hacks\AgenticAi\AI\tools'

# Get all Python files
python_files = glob.glob(os.path.join(tools_dir, '*.py'))

for filepath in python_files:
    try:
        # Read file with UTF-8 encoding
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace all emojis
        modified = False
        for emoji, replacement in replacements.items():
            if emoji in content:
                content = content.replace(emoji, replacement)
                modified = True
        
        # Write back if modified
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Fixed: {os.path.basename(filepath)}')
    except Exception as e:
        print(f'Error fixing {filepath}: {e}')

print('Done!')
