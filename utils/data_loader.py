import argparse

from langchain_community.document_loaders import PyMuPDFLoader


def extract_text_from_pdf(input_file: str, output_file: str):
    # Open the PDF file using the specified file_path
    loader = PyMuPDFLoader(input_file)
    document = loader.load()

    # Initialize an empty string to store extracted text
    pdf_text = ""

    # Loop through each page of the PDF
    for i in document:
        # Get the i-th page
        page = i.page_content
        # Extract text from the page and append it to pdf_text
        pdf_text += page
        # Add a newline after each page's text for readability
        pdf_text += "\n"

    # Specify the file path for the new text file
    file_path = output_file

    # Write the content to the text file
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(pdf_text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess doc")
    parser.add_argument('input_file_path', type=str)
    parser.add_argument('output_file_path', type=str)
    args = parser.parse_args()
    extract_text_from_pdf(args.input_file_path, args.output_file_path)
