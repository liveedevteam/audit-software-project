#!/usr/bin/env node
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");

const packageRoot = path.resolve(__dirname, "..");
const targetDir = path.join(os.homedir(), ".claude", "skills", "audit-software-project");

const filesToInstall = ["SKILL.md", "references", "assets"];

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

  console.log(
    `${existed ? "Updated" : "Installed"} audit-software-project skill at ${targetDir}`
  );
  console.log("Restart Claude Code (or start a new session) to pick it up.");
}

main();
