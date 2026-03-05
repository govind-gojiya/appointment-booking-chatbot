# Appointment Booking Chatbot

Helps users book appointments in the future within working hours (9 AM to 6 PM). The chatbot can also reschedule, cancel, and list bookings.

## LLM Options

1. **Hugging Face (Default)**  
   Add your Hugging Face API key to the `.env` file.

2. **Local Ollama**  
   Open `main.py`, comment out the `agent_huggingface` import, and uncomment the `agent_ollama` import to use a local Ollama model.  
   Download the `qwen2:7b` model (or update the model name inside `agent_ollama.py` based on the model you want to use).

3. **Groq**  
   Open `main.py`, comment out the `agent_huggingface` import, and uncomment the `agent` import to use Groq.  
   Add your Groq API key to the `.env` file.

## How to Run

- Clone the repository  
- Create a `.env` file and configure it based on the LLM you want to use (refer to `.env.example`)  
- Run `uv sync` (make sure `uv` is installed on your system)  
- Run `uv run streamlit run main.py`