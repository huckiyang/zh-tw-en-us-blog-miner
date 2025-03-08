# zh-tw-en-us-blog-miner

[huggingface](https://huggingface.co/datasets/huckiyang/zh-tw-en-us-nv-tech-blog-v1)

- run

```
python nv-blog.py
```

- loading

```
from datasets import load_from_disk, load_dataset

# Option 1: Load the dataset saved in Hugging Face's native disk format
dataset = load_from_disk("nvidia_blog_dataset")
print(dataset)
print(dataset['train'][0])  # Print the first record

# Option 2: Load the dataset from a JSON Lines file
dataset_json = load_dataset("json", data_files="nvidia_blog_dataset.jsonl")
print(dataset_json)
print(dataset_json['train'][0])
```
