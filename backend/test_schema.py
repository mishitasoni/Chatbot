import os
import glob
import json

paths = glob.glob(r'C:\Users\mishs\.openclaw\npm\**\protocol.schema.json', recursive=True)
with open("schema_result.txt", "w", encoding="utf-8") as f:
    f.write(f"Found {len(paths)} schemas\n")
    for p in paths:
        f.write(f"Schema: {p}\n")
        try:
            with open(p, "r", encoding="utf-8") as sf:
                schema = json.load(sf)
                # Find the connect params client id enum
                try:
                    client_id_enum = schema['definitions']['ConnectParams']['properties']['client']['properties']['id']['enum']
                    f.write(f"Allowed Client IDs: {client_id_enum}\n")
                except Exception as e:
                    f.write(f"Could not find enum: {e}\n")
        except Exception as e:
            f.write(f"Error reading {p}: {e}\n")
