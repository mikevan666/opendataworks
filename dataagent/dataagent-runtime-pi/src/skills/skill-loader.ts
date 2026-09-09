import fs from "node:fs/promises";
import path from "node:path";
import { Type } from "@earendil-works/pi-ai";

export interface SkillEntry {
  name: string;
  root_path: string;
}

export function createSkillTool(skills: SkillEntry[]): unknown {
  const allowedSkills = new Map<string, string>();
  for (const s of skills || []) {
    if (s.name && s.root_path) {
      allowedSkills.set(s.name, s.root_path);
      // Also allow resolving by folder basename if different
      const base = path.basename(s.root_path);
      if (base && !allowedSkills.has(base)) {
        allowedSkills.set(base, s.root_path);
      }
    }
  }

  const availableList = Array.from(allowedSkills.keys()).join(", ") || "(none)";

  return {
    name: "Skill",
    label: "Skill",
    description: `Load instructions, reference rules, and operational guidelines for an enabled skill. Available skills: ${availableList}`,
    parameters: Type.Object({
      skill_name: Type.String({
        description: `The exact name of the skill to load. Enabled: ${availableList}`,
      }),
    }),
    execute: async (_toolCallId: string, params: { skill_name: string }) => {
      const targetName = String(params?.skill_name || "").trim();
      const rootPath = allowedSkills.get(targetName);
      if (!rootPath) {
        return {
          content: [
            {
              type: "text",
              text: `Skill '${targetName}' is not enabled. Available skills: ${availableList}`,
            },
          ],
          details: { denied: true, available: Array.from(allowedSkills.keys()) },
          isError: true,
        };
      }

      const skillFilePath = path.join(rootPath, "SKILL.md");
      try {
        const content = await fs.readFile(skillFilePath, "utf8");
        return {
          content: [{ type: "text", text: content }],
          details: { skill_name: targetName, root_path: rootPath },
        };
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : String(err);
        return {
          content: [
            {
              type: "text",
              text: `Failed to read SKILL.md for skill '${targetName}': ${message}`,
            },
          ],
          details: { error: message },
          isError: true,
        };
      }
    },
  };
}
