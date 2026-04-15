# Skills Source Tree

仓库根目录的 `skills/` 是 OpenDataWorks 与 `opendataagent` 共享的唯一 Skill 源码目录。

约定：

- `skills/platform/*`：OpenDataWorks 平台能力
- `skills/generic/*`：通用 agent 能力
- `skills/bin/odw-cli`：平台能力唯一 CLI 入口
- `skills/lib/*`：平台 skill 共用运行时辅助模块

`opendataagent` 不直接编辑这里的内容。运行时和构建时会把这里的内容镜像到：

- `opendataagent/server/skills/bin`
- `opendataagent/server/skills/lib`
- `opendataagent/server/skills/bundled/*`

因此：

- 修改内置 skill 时只改根目录 `skills/`
- 不要手工修改 `opendataagent/server/skills/bundled/*`
