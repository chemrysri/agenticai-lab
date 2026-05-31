import fitz

from ollama_client import ask_ollama


MAX_PDF_CHARS_FOR_SUMMARY = 30000


def extract_pdf_text(file_path):
    document = fitz.open(file_path)

    extracted_parts = []

    for page_index, page in enumerate(document, start=1):
        page_text = page.get_text("text").strip()

        if page_text:
            extracted_parts.append(
                f"[Page {page_index}]\n{page_text}"
            )

    document.close()

    extracted_text = "\n\n".join(extracted_parts).strip()

    if not extracted_text:
        return (
            "No selectable text could be extracted from this PDF. "
            "It may be a scanned PDF or image-only document."
        )

    return extracted_text


def summarize_pdf_for_thread(file_name, extracted_text, model):
    text_for_summary = extracted_text

    if len(text_for_summary) > MAX_PDF_CHARS_FOR_SUMMARY:
        text_for_summary = (
            text_for_summary[:MAX_PDF_CHARS_FOR_SUMMARY]
            + "\n\n[Note: PDF text was truncated for summarization.]"
        )

    summary_messages = [
        {
            "role": "system",
            "content": (
                "You summarize uploaded PDFs for a private AI assistant. "
                "Create a compact but useful summary for future conversation. "
                "Preserve key facts, decisions, instructions, requirements, "
                "definitions, entities, numbers, and action items. "
                "Do not add information that is not in the PDF."
            ),
        },
        {
            "role": "user",
            "content": (
                f"PDF file name: {file_name}\n\n"
                "Extracted PDF text:\n"
                f"{text_for_summary}\n\n"
                "Return a useful structured summary."
            ),
        },
    ]

    return ask_ollama(
        messages=summary_messages,
        model=model,
    )