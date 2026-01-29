# Security Policy

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **thientquang@gmail.com**

You should receive a response within 48 hours.

### What to Include

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Any suggested fixes (optional)

## Security Considerations

### Authentication
- KumiAI uses the underlying Claude SDK authentication
- No separate API key management required
- Follow [Claude CLI setup](https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/red-team-with-prompt-shields) for authentication

### Agent Execution
- Agents can execute code and access files within project directories
- Only use KumiAI with trusted project content
- Review agent configurations before running sessions

### File System Access
- Agents operate within `~/.kumiai/projects/` directories
- File attachments are stored in project-specific folders
- Ensure proper file permissions on your system

### Local-First Design
- Intended for single-user, local development use
- No built-in authentication or multi-user support
- Database stored locally at `~/.kumiai/kumiai.db`

## Best Practices

1. **Trust your content** - Only work with projects and files you trust
2. **Review agent configs** - Check agent personalities and skills before use
3. **Back up your data** - Regularly backup `~/.kumiai/` directory
4. **Keep updated** - Watch for security updates in releases

---

**Thank you for helping keep KumiAI secure!**
