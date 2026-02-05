# 47 Doors Hackathon - Coach Talking Points

Prepared messaging for phase transitions and key concepts throughout the hackathon day.

---

## 1. Opening (Welcome)

### Key Message
Welcome to 47 Doors! Today you'll build a production-ready multi-agent AI system from scratch—not just learn concepts, but ship working code that demonstrates the future of enterprise AI architecture.

### Supporting Points
- **What you'll build**: A complete multi-agent system with RAG, tool use, orchestration, and cloud deployment
- **Why multi-agent**: Single LLM calls hit walls fast—real applications need specialized agents working together, each with focused capabilities
- **The progression**: Each lab builds on the last, from basic chat to deployed enterprise solution
- **Hands-on focus**: Less lecture, more coding—you'll have working code at each checkpoint
- **Success looks like**: By end of day, you'll have a deployed Azure application you can demo and extend

### Common Questions to Anticipate
- *"Do I need Azure experience?"* — No, we'll guide you through setup. Basic Python/TypeScript helps but isn't required.
- *"Can I use my own OpenAI key?"* — We're using Azure OpenAI for enterprise features, but concepts transfer to any provider.
- *"What if I fall behind?"* — Each lab has checkpoint code. You can always catch up and rejoin.
- *"Will I get the code afterward?"* — Yes, the full repository is yours to keep and extend.

---

## 2. Lab 01 → Lab 02 Transition

### Key Message
You've built a working chat agent—now let's give it superpowers. MCP (Model Context Protocol) is how we connect AI to the real world through standardized tool interfaces.

### Supporting Points
- **Why MCP matters**: It's the USB standard for AI tools—write once, use everywhere
- **From chat to action**: Your agent can now DO things, not just talk about them
- **Standardization wins**: MCP tools work across Claude, GPT, and other models without rewriting
- **Building blocks**: Each tool you add multiplies what your agent can accomplish
- **Real-world parallel**: Think of MCP like APIs for humans—structured ways to interact with systems

### Common Questions to Anticipate
- *"How is MCP different from function calling?"* — MCP is a protocol/standard; function calling is one implementation. MCP provides discovery, schemas, and cross-platform compatibility.
- *"Do I need to build my own MCP servers?"* — Not today—we'll use existing ones. Lab 07 (stretch) covers building custom servers.
- *"What tools are available?"* — Filesystem, web search, databases, APIs—the ecosystem is growing rapidly.

---

## 3. Lab 02 → Lab 03 Transition

### Key Message
Tools give agents capability, but specifications and constitutions give them purpose and boundaries. Spec-driven development means your agent knows WHAT to do, and constitutional AI ensures it does so safely.

### Supporting Points
- **Specs are contracts**: Clear specifications prevent agents from going off-script or hallucinating capabilities
- **Constitution as guardrails**: Define what your agent should and shouldn't do before it can surprise you
- **Testability**: Specs let you verify agent behavior systematically, not just hope it works
- **Enterprise requirement**: No production AI system ships without clear behavioral boundaries
- **Iterate safely**: Change specs to change behavior—much safer than prompt engineering alone

### Common Questions to Anticipate
- *"Isn't this just a system prompt?"* — Specs are more structured and testable. They define behavior contractually, not just suggestively.
- *"How strict are constitutional constraints?"* — They're guidelines the model follows strongly, but not hard blocks. Defense in depth matters.
- *"Can agents override their constitution?"* — Well-designed constitutions are very difficult to bypass, but security requires multiple layers.

---

## 4. Pre-Lunch Motivation (Before Lab 04)

### Key Message
RAG is where the magic happens—this is how your agent becomes an expert on YOUR data. The next lab is the technical heart of the hackathon, and it's worth the deep dive.

### Supporting Points
- **RAG = Real value**: Generic LLMs are commodities; RAG on your data is your competitive advantage
- **Beyond keyword search**: Semantic search understands meaning, not just matching words
- **Chunking strategy matters**: How you split documents dramatically affects retrieval quality
- **Azure AI Search power**: Enterprise-grade vector search with hybrid capabilities
- **Foundation for everything**: Every subsequent lab builds on the retrieval system you create here

### Common Questions to Anticipate
- *"Why not just put everything in the context window?"* — Cost, latency, and context limits. RAG scales to millions of documents.
- *"How do I know if retrieval is working well?"* — We'll cover evaluation metrics. Relevance scoring tells you retrieval quality.
- *"What about hallucination?"* — Good RAG reduces hallucination by grounding responses in retrieved facts.
- *"Can I use my own documents?"* — Absolutely! The system works with any text content.

---

## 5. Post-Lunch Energy (Before Lab 05)

### Key Message
You have agents, tools, specs, and retrieval—now orchestration ties it all together. This is where your system becomes more than the sum of its parts.

### Supporting Points
- **Almost there**: One lab to orchestration, one to deployment—you're on the home stretch
- **Orchestration = intelligence**: Deciding which agent handles what, when to retrieve, how to combine results
- **Patterns matter**: Router, chain, parallel execution—each pattern solves different problems
- **Error handling**: Real systems need graceful degradation when components fail
- **This is the architecture**: What you build here is how production multi-agent systems actually work

### Common Questions to Anticipate
- *"How do I decide which orchestration pattern to use?"* — Start simple (router), add complexity only when needed. We'll discuss tradeoffs.
- *"What about latency with multiple agents?"* — Parallel execution and caching help. We'll cover optimization strategies.
- *"How do agents communicate?"* — Through the orchestrator—it manages context and routes messages.

---

## 6. Lab 05 → Lab 06 Transition

### Key Message
Deployment makes it real—code on your laptop doesn't help anyone. Azure gives you enterprise infrastructure, security, and scalability without the ops burden.

### Supporting Points
- **From prototype to production**: Same code, now running in the cloud with real infrastructure
- **Azure benefits**: Managed identity, private endpoints, monitoring, scaling—enterprise requirements handled
- **Infrastructure as Code**: Bicep templates mean reproducible, version-controlled deployments
- **Security by default**: Azure OpenAI and AI Search integrate with enterprise security controls
- **Demo-ready**: After this lab, you can show your system to stakeholders with a real URL

### Common Questions to Anticipate
- *"How much will this cost?"* — We're using free tiers and minimal resources. Pennies for the hackathon.
- *"Can I deploy to AWS/GCP instead?"* — Concepts transfer; specific services differ. Today we focus on Azure.
- *"What about CI/CD?"* — Great next step! The Bicep templates work with any CI/CD system.
- *"How do I clean up resources?"* — We'll cover resource group deletion at the end.

---

## 7. Closing & Stretch Goal Intro

### Key Message
You did it—you built and deployed a production multi-agent AI system in one day. That's not a toy; that's a foundation you can extend into real applications.

### Supporting Points
- **Celebrate the accomplishment**: Multi-agent RAG with cloud deployment is genuinely sophisticated
- **What you built**: Chat agent → MCP tools → Specs/Constitution → RAG → Orchestration → Azure deployment
- **Stretch goal (Lab 07)**: Building your own MCP server takes you from consumer to producer of AI tools
- **Take it further**: Add more agents, connect more data sources, build domain-specific tools
- **Community continues**: Slack channel, GitHub repo, office hours—keep building together

### Common Questions to Anticipate
- *"What should I build next?"* — Connect to your real data sources. Build tools for your actual workflows.
- *"How do I learn more about MCP?"* — Anthropic's MCP documentation, plus the stretch lab if you have time.
- *"Can I use this at work?"* — Yes! The architecture patterns are production-ready. Adapt to your security requirements.
- *"Where do I get help after today?"* — GitHub issues, community Slack, and documentation in the repo.

---

## Quick Reference: Timing Cues

| Transition | Approximate Time | Energy Level |
|------------|------------------|--------------|
| Opening | 9:00 AM | High excitement |
| Lab 01 → 02 | 10:00 AM | Building momentum |
| Lab 02 → 03 | 10:30 AM | Deepening understanding |
| Break (→ Lab 04) | 11:15 AM | Refresh before deep dive |
| Lunch (→ Lab 05) | 12:30 PM | Re-fuel |
| Lab 05 → 06 | 2:30 PM | Home stretch energy |
| Closing | 4:00 PM | Celebration + inspiration |

---

## Coach Tips

- **Read the room**: Adjust depth based on participant experience level
- **Encourage questions**: Transitions are natural pause points for clarification
- **Celebrate progress**: Each lab completion is a real accomplishment
- **Stay positive on struggles**: Getting stuck is part of learning—normalize it
- **Point to resources**: The repo has extensive documentation for self-service help
