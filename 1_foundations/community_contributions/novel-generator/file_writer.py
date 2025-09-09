import os

def write_novel_to_file(result):
  # Output result to file
  lines = result.strip().splitlines()
  generated_title = "untitled_novel"
  for line in lines:
      if line.strip():  # skip empty lines
          generated_title = line.strip()
          break

  # Sanitize title for filename
  filename_safe_title = ''.join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in generated_title).strip().replace(' ', '_')
  output_path = os.path.abspath(f"{filename_safe_title}.txt")

  # Save to file
  with open(output_path, "w", encoding="utf-8") as f:
      f.write(result)

  # Show full path
  print(f"\n📘 Novel saved to: {output_path}")
