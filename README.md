# Project Setup Guide

## Prerequisites
To run this project successfully, ensure that you have installed the following dependencies:

### 1. Install Ollama
Ollama is required to run LLM models. Follow the installation instructions based on your operating system:

- **Windows**: [Download and install Ollama](https://ollama.com/download/windows)
- **Mac**: [Download and install Ollama](https://ollama.com/download/mac)

Once installed, start the Ollama server by running:
```sh
ollama serve
```
Then, pull the required models:
```sh
ollama pull llama3
ollama pull mxbai-embed-large
```

### 2. Install Miniconda
Miniconda is used for managing the project environment. Download and install Miniconda from:
- [Miniconda Installation Guide](https://docs.conda.io/en/latest/miniconda.html)

After installation, create a new environment:
```sh
conda create --name my_env python=3.9
```
Activate the environment:
```sh
conda activate my_env
```

## Running the Project
Follow these steps to set up and run the project:

1. Activate the Conda environment:
   ```sh
   conda activate my_env
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Remove cached files and databases:
   ```sh
   rm -rf LLM/__pycache__ LLM/chromadb
   ```
4. Navigate to the `LLM` directory and run the main script:
   ```sh
   cd LLM
   python main.py
   ```
5. Navigate to the `server` directory and start the server:
   ```sh
   cd ../server
   yarn start
   ```

## Notes
- Ensure that **Ollama** is running before starting the project.
- If you encounter dependency issues, consider recreating the Conda environment using the provided instructions.
- For additional support, refer to the official documentation of Ollama, Miniconda, and the project dependencies.

