with open(r"C:\Users\naras\Downloads\mlsentinel.2026-07-29.private-key.pem") as f:
    content = f.read()

escaped = content.replace("\n", "\\n")

with open("key_output.txt", "w") as out:
    out.write(f"GITHUB_APP_PRIVATE_KEY={escaped}\n")

print("Done — check key_output.txt")