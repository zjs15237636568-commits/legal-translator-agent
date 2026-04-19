# 贡献指南 / Contributing

感谢你对 **Legal Translator Agent** 的关注！本项目欢迎所有形式的贡献：Bug 报告、功能建议、代码 PR、文档改进、术语库扩充等。

## 1. 提交 Issue

提 Issue 前请先搜索现有 issues 避免重复。建议使用以下模板：

- **Bug 报告**：复现步骤 / 期望行为 / 实际行为 / 运行环境（OS、Python、Node 版本）/ 截图或日志
- **功能建议**：使用场景 / 方案描述 / 可选的替代方案

## 2. 本地开发

```bash
git clone https://github.com/<your-name>/legal-translator-agent.git
cd legal-translator-agent
./start.sh        # 首次会自动安装依赖
```

- 后端：`backend/`，FastAPI + SSE；热重载开启
- 前端：`frontend/`，Vue 3 + Vite；HMR 开启

## 3. 代码规范

### Python
- 遵循 PEP 8，使用 4 空格缩进
- 公共函数需带类型注解（typing）与 docstring
- 异步函数优先，阻塞 IO 请放 `asyncio.to_thread`

### JavaScript / Vue
- 2 空格缩进，单引号
- 组件使用 `<script setup>`
- 状态管理统一走 Pinia，不在组件内乱放全局变量

## 4. 提交 Pull Request

1. Fork 仓库并基于 `main` 创建特性分支：`feat/xxx` / `fix/xxx` / `docs/xxx`
2. 提交信息遵循 [Conventional Commits](https://www.conventionalcommits.org/)：
   ```
   feat(translator): support resume from breakpoint
   fix(glossary): case-insensitive word boundary
   docs(readme): add deployment guide
   ```
3. PR 描述需包含：变更动机、影响范围、测试方法、截图（若涉及 UI）
4. 确保 `read_lints`（或本地 `ruff` / `eslint`）通过

## 5. 安全披露

如发现安全漏洞（涉及 API Key 泄露、RCE 等），请勿直接提 Issue，请通过邮件私下联系维护者。

## 6. 行为准则

所有参与者需遵守 [Contributor Covenant](https://www.contributor-covenant.org/) 行为准则，营造友善、包容的社区氛围。
