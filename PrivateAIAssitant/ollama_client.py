import requests

from config import OLLAMA_URL


def ask_ollama(messages, model):
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120,
        )

        response.raise_for_status()

        data = response.json()

        return data["message"]["content"]

    except requests.exceptions.ConnectionError:
        return (
            "I could not connect to Ollama. "
            "Please make sure Ollama is installed and running."
        )

    except requests.exceptions.Timeout:
        return "The model took too long to respond. Try a smaller model."

    except Exception as error:
        return f"Something went wrong: {error}"