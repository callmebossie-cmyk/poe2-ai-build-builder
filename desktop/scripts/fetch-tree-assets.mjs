import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile, rename } from "node:fs/promises";

const revision = "bd87e6512c92b868542eddfb1ba4ea8b6dc2da36";
const directory = new URL("../public/tree/", import.meta.url);
const files = {
  "skills.json": "a7b80d577d2f81fa3c475e432b21225951272dcc3687e506143cd850c2f9f72e",
  "skills.webp": "b7ee18066709a323aef0dd14e4c4c31fffb7adca7db2cfffef6a6bfb4c745b89",
};
const hash = bytes => createHash("sha256").update(bytes).digest("hex");
await mkdir(directory, { recursive: true });
for (const [name, expected] of Object.entries(files)) {
  const destination = new URL(name, directory);
  try {
    if (hash(await readFile(destination)) === expected) continue;
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }
  const response = await fetch(
    `https://raw.githubusercontent.com/grindinggear/poe2-skilltree-export/${revision}/assets/${name}`,
    { signal: AbortSignal.timeout(60000) },
  );
  if (!response.ok) throw new Error(`Could not fetch ${name}: HTTP ${response.status}`);
  const bytes = Buffer.from(await response.arrayBuffer());
  if (hash(bytes) !== expected) throw new Error(`Checksum mismatch: ${name}`);
  const temporary = new URL(name + ".download", directory);
  await writeFile(temporary, bytes);
  await rename(temporary, destination);
  console.log(`Fetched verified GGG atlas: ${name}`);
}
