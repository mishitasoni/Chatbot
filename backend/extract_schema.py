import re

def extract_tables():
    with open(r'C:\Users\mishs\.openclaw\state\openclaw.sqlite', 'rb') as f:
        data = f.read()
    
    # Extract strings from binary data
    strings = re.findall(b'[ -~]{4,}', data)
    
    create_tables = []
    for s in strings:
        try:
            text = s.decode('utf-8', errors='ignore')
            if 'CREATE TABLE' in text.upper():
                create_tables.append(text)
        except:
            pass
            
    with open('schema_strings.txt', 'w', encoding='utf-8') as f:
        for t in create_tables:
            f.write(f"{t}\n\n")

if __name__ == '__main__':
    extract_tables()
