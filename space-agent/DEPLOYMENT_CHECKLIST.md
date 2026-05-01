# Deployment Checklist

- [ ] .env is not committed
- [ ] .env.local is not committed
- [ ] OPENAI_API_KEY is not present in source code
- [ ] OPENAI_API_KEY is configured only as an environment variable
- [ ] No NEXT_PUBLIC_OPENAI_API_KEY is used
- [ ] outputs/ is ignored by Git
- [ ] Generated DOCX/PDF files are not committed
- [ ] APP_PASSWORD is set for demo deployments
- [ ] App has generation limits
- [ ] App has input length limits
- [ ] App handles missing API key gracefully
- [ ] App handles OpenAI API errors gracefully
- [ ] Deployment URL protection has been reviewed
- [ ] README includes deployment security notes