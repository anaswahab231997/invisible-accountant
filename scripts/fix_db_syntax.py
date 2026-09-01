def fix():
    with open('db.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    with open('db.py', 'w', encoding='utf-8') as f:
        for i, line in enumerate(lines):
            if "await conn.execute(" in line and i < len(lines)-1 and lines[i+1].strip() == "":
                # Check if it's the bad one
                if "CREATE TABLE IF NOT EXISTS intake_queue" in lines[i+2]:
                    continue # Skip this line
            f.write(line)
            
if __name__ == "__main__":
    fix()
