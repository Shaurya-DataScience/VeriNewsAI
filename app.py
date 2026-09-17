import os
import sys

# Add backend directory to Python system path
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from backend.main import app as fastapi_app
import gradio as gr

# Build an interactive status dashboard for the Hugging Face Space
with gr.Blocks(title="VeriNews AI Verification Engine") as demo:
    gr.Markdown("# 🛡️ VeriNews AI Cloud Engine")
    gr.Markdown("**Enterprise Fact Verification & Grounding Platform** is live and running.")
    gr.Markdown("""
    ### 🔗 Cloud API Navigation:
    - 📚 **Interactive Swagger API Docs:** [/docs](/docs)
    - 🔍 **System Health Check:** [/health](/health)
    - 🌐 **Production Web Client:** [VeriNews AI Frontend](https://verinews-ai.vercel.app)
    """)

# Mount Gradio onto the existing FastAPI application
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
