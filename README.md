## anirudhsivakumar-langchain-appliedai-takehome

## Built by **Anirudh Sivakumar**
# Hi Palash & Brace! Thank you for giving me the opportunity to interview for LangChain, I hope you guys like and approve of what I've built!

## My Approach

I'm building this agent to demonstrate my understanding of LangGraph and LangChain's powerful capabilities. My goal is to showcase how these frameworks can be used to create sophisticated AI agents with proper architecture patterns.

**LangGraph Patterns I'm gonna be using:**
- **Serial Nodes**: Sequential file operations (read → modify → write)
- **Conditional Edges**: Intent-based routing (chat vs edit actions)
- **State Management**: TypedDict with reducers for conversation history
- **Memory & Persistence**: MemorySaver for maintaining context across sessions

- **Parallel Execution**: Multi-file operations using Send() for concurrent processing
- **Reducers**: Aggregating results from parallel branches
- **Interrupts**: Human-in-the-loop approval for sensitive operations
- **Time Travel**: Debugging and replaying agent decisions

This is my way of showing that I understand not just how to use these tools, but when and why to use each pattern/capability the LangGraph framework has to offer.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

## Run

```bash
python3 -m cli.main
```


