#!/usr/bin/env node
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");

const packageRoot = path.resolve(__dirname, "..");
const args = process.argv.slice(2);

if (args.includes("--help") || args.includes("-h")) {
  console.log(
    "Usage: npx audit-software-project [--path <skills-dir>]\n" +
      "Copies the skill into ~/.claude/skills/audit-software-project (or <skills-dir>)."
  );
  process.exit(0);
}

// --path <dir> installs into a custom skills directory instead of ~/.claude/skills
let skillsRoot = path.join(os.homedir(), ".claude", "skills");
const pathFlag = args.indexOf("--path");
if (pathFlag !== -1) {
  if (!args[pathFlag + 1]) {
    console.error("--path needs a directory");
    process.exit(2);
  }
  skillsRoot = path.resolve(args[pathFlag + 1]);
}

const targetDir = path.join(skillsRoot, "audit-software-project");
const filesToInstall = ["SKILL.md", "references", "assets", "scripts"];
const optionalFiles = ["STATUS.md", "CHANGELOG.md"];

function makeScriptsExecutable(dir) {
  if (!fs.existsSync(dir)) return;
  for (const name of fs.readdirSync(dir)) {
    if (name.endsWith(".sh") || name.endsWith(".py")) {
      fs.chmodSync(path.join(dir, name), 0o755);
    }
  }
}

function main() {
  const existed = fs.existsSync(targetDir);

  fs.mkdirSync(targetDir, { recursive: true });

  for (const name of filesToInstall) {
    const src = path.join(packageRoot, name);
    const dest = path.join(targetDir, name);
    if (!fs.existsSync(src)) {
      console.error(`Missing expected file in package: ${name}`);
      process.exit(1);
    }
    fs.rmSync(dest, { recursive: true, force: true });
    fs.cpSync(src, dest, { recursive: true });
  }
  for (const name of optionalFiles) {
    const src = path.join(packageRoot, name);
    if (fs.existsSync(src)) fs.copyFileSync(src, path.join(targetDir, name));
  }
  makeScriptsExecutable(path.join(targetDir, "scripts"));

  console.log(
    `${existed ? "Updated" : "Installed"} audit-software-project skill at ${targetDir}`
  );
  console.log("Restart Claude Code (or start a new session) to pick it up.");
}

main();
