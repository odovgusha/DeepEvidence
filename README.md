DeepEvidence
A Flask-based retrieval-augmented Q&A app for a personal library of scientific papers, built around induced pluripotent stem cell (iPSC) research. Drop in PDFs, ask questions, get answers grounded in (and cited from) only your indexed corpus.
Includes a self-contained evaluation harness for comparing prompting techniques and models side by side.

What it does

Upload any PDF; text is extracted and chunked.
Index chunks as vector embeddings in a local FAISS store.
Ask questions in a chat interface; retrieval pulls the most relevant chunks and an LLM answers using only those chunks, with [SOURCE N] citations.
Search the corpus directly (vector search, no LLM).
Evaluate different prompting techniques and models against a fixed question bank, with token usage, cost, latency, and an LLM-as-judge quality score.


Stack

Backend: Flask, SQLAlchemy (SQLite)
Retrieval: FAISS, LangChain (langchain-community, langchain-openai)
Embeddings: OpenAI text-embedding-3-small
LLM: OpenAI gpt-4.1-mini (configurable)
PDF: pdfplumber
Templates: Jinja2


Repository layout
DeepEvidence/
├── app.py                  # Flask app: routes for upload, chat, search, papers
├── models.py               # SQLAlchemy models: Paper, Thread, Message
├── data_manager.py         # CRUD wrapper around the models
├── pdf_parser.py           # Batch script: search PubMed + fetch open-access PDFs
├── services/
│   ├── pdf.py              # extract_text via pdfplumber
│   ├── vector_store.py     # FAISS index lifecycle: build, load, search
│   └── rag_chain.py        # Production RAG prompt + answer generation
├── templates/              # Jinja2 templates for chat UI, paper list, search, etc.
├── faiss_index/            # FAISS index files (generated)
├── uploads/                # User-uploaded PDFs (generated)
├── ipsc_papers_full/       # iPSC corpus pulled by pdf_parser.py
├── instance/db.sqlite      # SQLite database (generated)
├── eval/                   # Standalone evaluation harness (see below)
└── requirments.txt

Setup
bashgit clone https://github.com/odovgusha/DeepEvidence.git
cd DeepEvidence

python -m venv .venv
.venv\Scripts\activate         # Windows
# source .venv/bin/activate    # macOS / Linux

pip install -r requirments.txt
Create a .env file at the repo root with your OpenAI API key:
OPENAI_API_KEY=sk-...

Running the app
bashpython app.py
Then open http://localhost:5000.
Available routes
RouteMethodPurpose/GETHome — list of indexed papers/uploadPOSTUpload a PDF (extracts text, indexes chunks)/papers/view/<id>GETView a single paper/papers/edit/<id>GET/POSTRename a paper/papers/delete/<id>POSTDelete a paper/papersGETJSON list of papers/searchGET/POSTVector search across the corpus (no LLM)/chatGETList chat threads/chat/createPOSTCreate a new chat thread/chat/<thread_id>GET/POSTChat with the corpus in a thread (RAG-grounded)/debugGETDump of all papers, threads, and messages

How RAG is wired

Ingest (/upload):

services/pdf.py extracts text via pdfplumber.
services/vector_store.add_paper_to_index chunks with RecursiveCharacterTextSplitter (chunk size 500, overlap 100) and embeds each chunk with text-embedding-3-small.
Chunks are stored in FAISS at faiss_index/. Each chunk's metadata links it back to the paper.


Ask (/chat/<thread_id>):

User message → vector search returns top-5 chunks.
services/rag_chain.generate_answer builds a prompt with the chunks, recent message history, and the question.
The system prompt enforces: answer only from retrieved data; combine sources; cite as [SOURCE N].
Answer is saved to the SQLite Message table.




Evaluation harness (eval/)
A standalone harness for comparing prompting techniques and models on a fixed question bank. It does not modify or depend on services/rag_chain.py — you can run it without touching production code.
What it measures
For each (model, technique, question) cell:

the full prompt that was sent to the model (logged)
the answer the model produced (logged)
latency (wall-clock time around the model call)
input/output/total tokens (from OpenAI's billing-grade usage report)
USD cost (computed from eval/pricing.py)
quality scored by an LLM-as-judge on three 1–5 axes:

faithfulness — every claim supported by the retrieved context
citation_accuracy — claims cite the correct [SOURCE N]
completeness — covers the relevant material across all retrieved chunks



Default grid
pythonMODELS     = ["gpt-4.1-mini", "gpt-4o-mini"]
TECHNIQUES = ["zero_shot", "few_shot"]
JUDGE      = "gpt-4.1-mini"   # configurable; should be at least as strong as the test models
K          = 5                # retrieval depth held constant across configs
For 8 questions × 2 models × 2 techniques you get 32 answer calls + 32 judge calls = 64 API calls per run, typically a few cents total.
Running it
bash# 1. Sanity-check API key + which models the project can call
python -m eval.check_access

# 2. Run the full grid
python -m eval.run_eval
Outputs
Each run writes to eval/runs/<UTC-timestamp>/:
FileContentsresults.csvOne row per call. Per-call metrics. Pivot in Excel by model/technique.summary.csvOne row per (model, technique). Aggregated metrics.results.jsonlFull audit trace: rendered prompt, answer, judge rationale, retrieved context.
A summary table is also printed to stdout at the end of each run.
eval/ package layout
FilePurposeeval/run_eval.pyMain harness; entry point for python -m eval.run_eval.eval/judge.pyLLM-as-judge: 3-axis rubric, strict JSON output, fault-tolerant.eval/pricing.pyPer-model USD-per-million-token rates + estimate_cost_usd().eval/few_shot_examples.pyTwo worked Q&A exemplars used in the few-shot arm.eval/questions.jsonQuestion bank (8 iPSC questions). Edit to add/remove.eval/check_access.pyPings each candidate model with a 1-token call; reports access status.
Adding a new prompting technique

Add the new technique name to TECHNIQUES in eval/run_eval.py.
Add a branch in examples_for(technique) (or a new prompt-builder function) that returns the right prompt variant for that name.
Re-run.

Configuring the judge
If your project doesn't have access to the default judge model, set JUDGE_MODEL near the top of eval/run_eval.py to one you do have. eval/check_access.py lists which models are accessible. The judge should be at least as capable as the strongest model under test — using a weaker judge produces noisier scores.

Caveats

Outside-knowledge bleed-through: the system prompt forbids it, but the LLM occasionally adds connective sentences from training data. The eval's faithfulness score catches this.
Same-family judging bias: when the judge model is also one of the test models (e.g., both gpt-4.1-mini), expect a small upward bias on rows where the judge grades its own family. Within-model comparisons (zero-shot vs. few-shot for the same model) are unaffected.
Pricing in eval/pricing.py: verify against the live OpenAI pricing page before quoting cost numbers in a report. Rates may have changed since the file was last edited.
Sandbox environments: PyPI and api.openai.com may be blocked in some hosted dev environments. Run the eval from your local machine where the venv and FAISS index live.
