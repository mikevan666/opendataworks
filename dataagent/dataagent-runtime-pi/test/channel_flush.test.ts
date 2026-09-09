/**
 * Frames must survive process exit.
 *
 * Writes to a pipe are asynchronous. Once the pipe buffer fills — which it does
 * whenever the parent drains slowly, and the real parent persists every event
 * to MySQL before reading the next line — further writes queue in memory, and
 * process.exit() throws that queue away. The terminal event is the last frame
 * written, so losing the tail turns a completed run into CELL_LOSS carrying a
 * truncated answer.
 *
 * This spawns a real child writing through CellChannel into a real pipe, with a
 * parent that deliberately delays reading, and asserts nothing is lost.
 */

import test from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
// dist/test -> dist -> dist/src/protocol/channel.js
const channelModule = path.resolve(here, "..", "src", "protocol", "channel.js");

/** Child that emits `count` frames through CellChannel, then exits. */
function childSource(count: number, withFlush: boolean): string {
  return `
import { CellChannel } from ${JSON.stringify(channelModule)};
const channel = new CellChannel(process.stdin, process.stdout);
for (let i = 1; i <= ${count}; i++) {
  channel.send("run.event", { sequence: i, filler: "x".repeat(200) });
}
channel.send("run.settled", { terminal_status: "success", last_sequence: ${count} });
channel.close();
${withFlush ? "await channel.flush();" : ""}
process.exit(0);
`;
}

async function runChild(count: number, withFlush: boolean): Promise<string[]> {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "odw-flush-"));
  const file = path.join(dir, "child.mjs");
  fs.writeFileSync(file, childSource(count, withFlush), "utf-8");

  return new Promise<string[]>((resolve, reject) => {
    const child = spawn(process.execPath, [file], { stdio: ["pipe", "pipe", "inherit"] });
    let buffer = "";
    let reading = false;

    // Do not read immediately: let the pipe buffer fill, the way a parent busy
    // writing each event to the database does.
    setTimeout(() => {
      reading = true;
      child.stdout.on("data", (chunk: Buffer) => {
        buffer += chunk.toString("utf8");
      });
    }, 300);

    child.on("error", reject);
    child.on("close", () => {
      const finish = () => resolve(buffer.split("\n").filter((line) => line.trim()));
      // Give the late-attached reader a moment to drain whatever survived.
      if (reading) {
        setTimeout(finish, 100);
      } else {
        setTimeout(finish, 400);
      }
    });
  });
}

test("no frame is lost when the parent reads slowly", async () => {
  const count = 3000;
  const lines = await runChild(count, true);

  assert.equal(lines.length, count + 1, `expected ${count + 1} frames, got ${lines.length}`);

  const last = JSON.parse(lines[lines.length - 1]) as { type: string; payload: { last_sequence: number } };
  assert.equal(last.type, "run.settled", "the settle frame must survive exit");
  assert.equal(last.payload.last_sequence, count);

  const secondLast = JSON.parse(lines[lines.length - 2]) as { payload: { sequence: number } };
  assert.equal(secondLast.payload.sequence, count, "the final event must survive exit");
});

test("exiting without flushing does lose frames", async () => {
  // Pins the reason flush() exists. If this ever stops losing frames the
  // guarantee has moved elsewhere and the flush contract should be revisited
  // rather than silently trusted.
  const count = 3000;
  const lines = await runChild(count, false);

  assert.ok(
    lines.length < count + 1,
    `expected truncation without flush, but all ${lines.length} frames arrived`
  );
});
