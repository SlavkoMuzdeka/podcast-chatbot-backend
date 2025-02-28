import os
import tiktoken

# Initialize the tokenizer
enc = tiktoken.get_encoding("cl100k_base")


def calculate_tokens_in_file(file_path):
    """Calculate the number of tokens in a single file."""
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()
    num_tokens = len(enc.encode(text))
    return num_tokens


def calculate_tokens_in_directory(directory_path):
    """Calculate the total number of tokens in all .txt files in a directory."""
    total_tokens = 0
    num_of_files = 0
    pom_list = []
    for file_name in os.listdir(directory_path):
        if file_name.endswith(".txt"):
            file_path = os.path.join(directory_path, file_name)
            num_tokens = calculate_tokens_in_file(file_path)
            total_tokens += num_tokens
            pom_list.append(num_tokens)
            num_of_files += 1
    print(f"Total number of files: {num_of_files}")
    print(f"Total number of tokens: {total_tokens}")
    print(f"Max number of tokens: {max(pom_list)}")
    return total_tokens


# Directory containing your 50 .txt files
directory_path = "podcasts"

# Calculate tokens in all files
total_tokens = calculate_tokens_in_directory(directory_path)

# import data_loader

# total = 0
# docs = data_loader.load_and_split_text()
# values = []
# for doc in docs:
#     num_tokens = len(enc.encode(doc))
#     values.append(num_tokens)
#     total += num_tokens
# print(total)
# print(values)
# print(max(values))
# 84344
# How did you go from this into I'm
